from datetime import datetime
import json
import logging
from typing import Any, Callable, List
import uuid
from pydantic import ValidationError
from Agent.AgentSkillRepository import AgentSkillRepository
from Agent.AgentPromptHandler import AgentPromptHandler, PromptInput
from Agent.AgentResponse import AgentAction, AgentResponse
from Agent.AgentNames import AgentName
from Agent.AgentToolRepository import AgentToolRepository
from Agent.Utils import Utils
from LLM.LLM import LLM
from Skills.skill_utils.SkillSelector import SkillSelector
from Tasks.Task import Task, AgentLog, PlanStep
from Tasks.TaskState import State
from Tools.LoadSkillTool import LoadSkillOutput
from Tools.Tool import Tool, ToolOutput, ToolResult
from Tools.tool_utils.ToolCapability import ToolCapability
from Tools.tool_utils.ToolTag import ToolTag
from Tools.tool_utils.ToolSelector import ToolSelector
from Tools.Task.TaskFileUtils import TaskFileUtils
from Common.color_printer import info, error, wild

logger = logging.getLogger(__name__)
class BaseAgent:
    DEFAULT_ALLOWED_TAGS = [
        ToolTag.TASKS, 
        ToolTag.UTILITY, 
        ToolTag.SKILLS
    ]
    DEFAULT_ALLOWED_CAPABILITIES = [
        ToolCapability.UPDATE_TASKS, 
        ToolCapability.LOAD_SKILL
    ]
    DEFAULT_DENIED_CAPABILITIES = [
        ToolCapability.RESTRCITED_UNTIL_FURTHER_CLARIFICATION, 
        ToolCapability.CREATE_REPOSITORY, 
        ToolCapability.CREATE_BRANCH,
    ]
    GOAL_CHECKER_TOOLS = []
    
    def __init__(self, llm: LLM, tool_selector: ToolSelector, skill_selector: SkillSelector):
        self.name: str = ""
        self.agentName: AgentName = AgentName.UNKNOWN
        self.llm = llm
        self.skill_count_limit = 6
        self.token_prompt_limit = 30000
        self.validation_error: str = ""
        self.max_steps = 10
        self.promptHandler = AgentPromptHandler()
        self.toolRepository = AgentToolRepository(tool_selector)
        self.skillRepository: AgentSkillRepository = AgentSkillRepository(skill_selector)

    def prepare(self, prompt: str, task: Task | PlanStep | None = None):
        print(f"\n\n Preparing {self.name}")
        self.final_goal = prompt

        work_item = task if isinstance(task, Task) else prompt
        self.skillRepository.prepare(work_item)
        self.toolRepository.prepare()
        current_goal_task = work_item if not isinstance(task, PlanStep) else task
        self.promptHandler.prepare(prompt, self.get_current_goal(current_goal_task), self.max_steps, self.agentName)
        if task is not None and task.status in State.ready_states():
            TaskFileUtils.advance_task_state(task.id)

    def log(self, task_id: str, input: str, output: str):
        log = AgentLog(
            agent=self.agentName, input=input, output=output, timestamp=datetime.now().isoformat()
        )
        TaskFileUtils.append_log_to_task(task_id, log)

    def ReActObs_stream(self, task: Task | None, planStep: PlanStep | None = None) -> AgentResponse | None:
        tool_executions: list[tuple[ToolResult, int, AgentResponse]] = []
        run_time_prompt_injections: list[str] = []
        run_summary: list[tuple[str, Callable]] = [] # message, print_level

        for _ in range(self.max_steps):            
            step: int = _ + 1

            if ((step >= self.max_steps - 3 or not self.skillRepository.can_load_skills()) and not self.promptHandler.can_load_skills):
                self.toolRepository.disable_tools([ToolCapability.LOAD_SKILL], [ToolTag.SKILLS])
                self.promptHandler.can_load_skills = False

            promptInput: PromptInput = PromptInput(
                tools = self.toolRepository.tools,
                skills = self.skillRepository.skills,
                allowed_skills = self.skillRepository.get_allowed_skill_nodes(),
                skill_limit = self.skillRepository.skill_count_limit,
                tool_executions = tool_executions,
                step = step,
                run_time_prompt_injections = ("\n".join(run_time_prompt_injections))
            )

            prompt = self.promptHandler.build_prompt(promptInput)

            llm_response = self.llm.stream_print_and_wait(prompt)
            cleaned_buffer = Utils.clean_and_parse_json(llm_response) 
            try:
                # 1. First attempt strict JSON parsing natively via Pydantic
                parsed = AgentResponse.model_validate_json(cleaned_buffer)
            except ValidationError as json_err:
                info("AgentResponse.model_validate_json failed. Attempting structural recovery...")
                
                try:
                    # 2. Safely parse Pythonic anomalies (like None, True, False) using json or eval
                    normalized_str = cleaned_buffer.replace(": None", ": null").replace(": True", ": true").replace(": False", ": false")
                    dict_payload = json.loads(normalized_str)
                    parsed = AgentResponse.model_validate(dict_payload)
                    
                except json.JSONDecodeError as decode_err:
                    # Construct an explicit explanation of the bad characters
                    detailed_msg = (
                        f"CRITICAL: The response contains invalid JSON syntax.\n"
                        f"Details: {decode_err.msg} at line {decode_err.lineno}, column {decode_err.colno}.\n"
                        f"Common fix: Ensure you are using true JSON (e.g., 'null' instead of 'None', and normal double quotes)."
                    )
                    error(detailed_msg)
                    run_summary.append((f"Step {step}: {detailed_msg} \n", error))
                    run_time_prompt_injections.append(detailed_msg)
                    continue
                    
                except ValidationError as dict_err:
                    detailed_msg = (
                        f"CRITICAL: JSON syntax is valid, but the schema fields failed validation.\n"
                        f"Validation Errors:\n{dict_err}"
                    )
                    error(detailed_msg)
                    run_time_prompt_injections.append(detailed_msg)
                    run_summary.append((f"Step {step}: {detailed_msg} \n", error))
                    continue

            parsedAction: AgentAction = AgentAction.from_string(parsed.action) 
            if parsed and parsedAction == AgentAction.Tool and parsed.tool_name:
                tool = self.toolRepository.get_tool(parsed.tool_name)
                if not tool:
                    error("The tool does not exist")
                    run_summary.append((f"Step {step}: The tool does not exist \n", error))
                    run_time_prompt_injections.append("The tool does not exist \n")
                    continue

                if parsed.input is None and tool.model_requires_input():
                    error("Tool expected input, but parsed.input is None")
                    run_summary.append((f"Step {step}: Tool expected input, but parsed.input is None \n", error))
                    run_time_prompt_injections.append("when running a tool, you must provide an input - atleast an empty json object. \n")
                    continue

                if parsed.input is None:
                    parsed.input = {}
                    info("Input is set to empty object")

                if ToolTag.TASKS in tool.tags:
                    self.__task_tool_input_injections(parsed.input, task, tool)

                result = self._execute_tool(parsed, tool)
                tool_executions.append((result.model_copy(), step, parsed.model_copy()))
                run_summary.append((Utils.to_run_time_executions(result, step, parsed) + "\n", Utils.get_printer_for_tool_executions(result)))

                if result and result.data and result.data.success == False:
                    run_time_prompt_injections.append(f"Tool [{tool.name}] executed, but failed to resolve. Error: {result.data.message} \n")
                elif result and not result.data and result.error:
                    run_time_prompt_injections.append(f"Tool [{result.error.tool}] failed: {result.error.error} \n")

                Utils.print_run_time_executions(result, step, parsed)

                if parsed.tool_name == "LoadSkillTool" and isinstance(result.data, LoadSkillOutput):
                    if result and result.data and result.data.skill_nodes:
                        self.skillRepository.add_skills(result.data.skill_nodes, result.data.skill_keywords)
                
            elif parsed.action == "final":
                wild(f"AGENT RUN SUMMARY:\n")
                for summary in run_summary:
                    self.print_summary(*summary)


                    # Utils.print_run_time_executions(*execution)
                # for execution_tool_result, execution_tool, execution_response in tool_executions_raw:
                    # tool_copy = execution_tool_result.model_copy()
                    # parsed_copy = execution_response.model_copy()
                    # Utils.print_run_time_executions(execution_tool_result, execution_tool, execution_response)
                
                return parsed

        wild(f"AGENT RUN SUMMARY:\n")        
        # for execution in tool_executions:
        #     Utils.print_run_time_executions(*execution)
        for summary in run_summary:
            self.print_summary(*summary)
        # for tool_result, steps, response in tool_executions_raw:
            # tool_copy = tool_result.model_copy()
            # parsed_copy = response.model_copy()
            # Utils.print_run_time_executions(tool_result, steps, response)
        
        print("ReAct did not finish")
        return None

    def print_summary(self, string: str, Callable: Callable) -> None:
        Callable(string)

    def __task_tool_input_injections(self, input: dict[str, Any], task: Task | None, tool: Tool):
        prompt_taskid = input.get("task_id")
        if prompt_taskid and isinstance(prompt_taskid, str) and not self.is_valid_uuid(prompt_taskid) and task:
            input["task_id"] = task.id

        tool_requires_agent_name = "agent_name" in tool.input_model.model_fields
        if tool_requires_agent_name:
            input["agent_name"] = self.name

    # def get_tool_warning(self, tool_executions_raw: list[tuple[ToolResult, int, AgentResponse]]) -> str:
    #     history_length = 3
    #     threshold = 2

    #     if len(tool_executions_raw) < history_length:
    #         return ""

    #     # Get the last 3 execution tuples and count the tool names
    #     last_executions = tool_executions_raw[-history_length:]
    #     tool_counts = collections.Counter(response.tool_name for _, _, response in last_executions)

    #     # Find all tools that met or exceeded the threshold
    #     offending_tools = [tool for tool, count in tool_counts.items() if count >= threshold and tool]

    #     if offending_tools:
    #         tool_names_formatted = " | ".join(offending_tools)
    #         return (
    #             f"\nSYSTEM WARNING: You have called '{tool_names_formatted}' multiple times without making progress. "
    #             f"You are strictly forbidden from calling '{tool_names_formatted}' on this step. Choose a different tool to break the loop.\n"
    #         )

    #     return ""

    # def __disable_tools(self, toolCapabilities: list[ToolCapability] | None, tooltags: list[ToolTag] | None) -> None:
    #     if toolCapabilities:
    #         for capability in toolCapabilities:
    #             if capability not in self.denied_capabilities:
    #                 self.denied_capabilities.append(capability)
    #                 print(f"Disabling capability: {capability}")
    #             else:
    #                 print(f"Capability {capability} already disabled.")

    #             if capability in self.allowed_capabilities:
    #                 self.allowed_capabilities = [c for c in self.allowed_capabilities if c != capability]
    #                 print(f"Removing all instances of capability from allowed: {capability}")
                    
    #     if tooltags:
    #         for tag in tooltags:
    #             if tag in self.allowed_tags:
    #                 self.allowed_tags = [t for t in self.allowed_tags if t != tag]
    #                 print(f"Disabling tag: {tag}")
    #             else:
    #                 print(f"Tag {tag} already disabled or not present.")

    #     self.tools = self.tool_selector.select(self)

    def is_valid_uuid(self, val: str) -> bool:
        try:
            return bool(uuid.UUID(str(val)))
        except (ValueError, TypeError, AttributeError):
            return False

    # def _add_skills(self, skillNodes: list[SkillNode] | None, skill_tags: list[str] | None = None) -> None:
    #     if skillNodes and skill_tags:
    #         for skill_node in skillNodes:
    #             self._add_skill(skill_node)
    #         for skill_tag in skill_tags:
    #             self._add_skill(None, skill_tag)

    # def _add_skill(self, skillNode: SkillNode | None, skill_tag: str | None = None) -> None:
    #     if skillNode and skillNode.name:
    #         if skillNode.name not in self.skill_name_added:
    #             self.skills.append(skillNode)
    #             self.skill_name_added.add(skillNode.name)
    #             print(f"Adding {skillNode.name} to the skill list.")
    #         else: 
    #             print(f"Skill {skillNode.name} already added.")
    #     elif skill_tag and isinstance(skill_tag, str):
    #         if skill_tag not in self.skill_keywords_added:
    #             self.skill_keywords_added.add(skill_tag)
    #     else:
    #         print(f"Skill node or skill tag is None. \n")


    def run(self, task: Task | str) -> Task:
        raise NotImplementedError("Subclasses must implement this method")

    def get_current_goal(self, task: Task | PlanStep | str) -> str:
        raise NotImplementedError("Subclasses must implement this method")

    def _execute_tool(self, parsed: AgentResponse, tool: Tool[Any, Any] | None) -> ToolResult[ToolOutput]:

        if not tool:
            raise Exception(f"Tool not found: {parsed.tool_name}")

        if parsed.input is None:
            raise Exception("Input was null, but must be a dict -> \"input\":{}")

        parsed_input = {}
        # Case 1: JSON string → dict
        if isinstance(parsed.input, str):
            try:
                parsed_input = json.loads(parsed.input)
            except json.JSONDecodeError as e:
                raise Exception(f"Invalid JSON input: {e}")

        # Case 2: Already dict → OK
        elif isinstance(parsed.input, dict):
            parsed_input = parsed.input
            pass

        # Case 3: Pydantic model → convert to dict
        elif hasattr(parsed.input, "model_dump"):
            parsed_input = parsed.input.model_dump()

        # Case 4: Other (invalid)
        else:
            raise Exception(f"Tool input must be a dictionary or JSON string, got {type(parsed.input)}")

        return tool.__call__(parsed_input)

    def _reload_task(self, task_id: str) -> Task:
        task = TaskFileUtils.load_task(task_id)
        return task

    def _reload_planStep(self, task: Task, plan_step_id: str) -> PlanStep:
        planStep = task.get_planstep_by_id(plan_step_id)
        if not planStep: 
            raise Exception("Reloading planstep resulted in None")
        return planStep