import ast
from datetime import datetime
import json
import os
import re
from typing import Any, Dict, Type
import uuid
from Agent.AgentResponse import AgentAction, AgentResponse
from Agent.AgentNames import AgentName
from LLM.LLM import LLM
from Skills.skill_utils.SkillNode import SkillNode
from Skills.skill_utils.SkillSelector import SkillSelector
from Tasks.Task import Task, AgentLog, PlanStep
from Tasks.TaskState import State
from Tools.LoadSkillTool import LoadSkillOutput
from Tools.Tool import Tool, ToolOutput, ToolResult
from Tools.tool_utils.ToolCapability import ToolCapability
from Tools.tool_utils.ToolTag import ToolTag
import tiktoken

from Tools.tool_utils.ToolSelector import ToolSelector
import logging

from Tools.Task.TaskFileUtils import TaskFileUtils


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
        self.tool_selector = tool_selector
        self.skill_selector = skill_selector
        self.template = ""
        self.skill_count_limit = 6
        self.token_prompt_limit = 30000
        self.allowed_tags = self.DEFAULT_ALLOWED_TAGS.copy()
        self.allowed_capabilities = self.DEFAULT_ALLOWED_CAPABILITIES.copy()
        self.denied_capabilities = self.DEFAULT_DENIED_CAPABILITIES.copy()
        self.goal_checker_tools: list[Type[Tool]] = self.GOAL_CHECKER_TOOLS.copy()
        self.validation_error: str = ""
        self.tools: Dict[str, Tool] = {}
        self.skill_name_added: set[str] = set()
        self.skill_keywords_added: set[str] = set()
        self.skills: list[SkillNode] = []
        self.max_steps = 25
        self.final_goal = ""
        
    def prepare(self, prompt: str, task: Task | PlanStep | None = None):
        print(f"\n\n Preparing {self.name}")
        self.final_goal = prompt
        
        if isinstance(task, Task):
            print(f"with task: \n- TaskId: {task.id} \n- TaskTitle: {task.title} \n\n")
        elif isinstance(task, PlanStep):
            print(f"With planstep: {task.id} \n\n")

        self.tools = self.tool_selector.select(self)

        if task is not None:
            if isinstance(task, Task):
                skills = self.skill_selector.select(task)
                if task.status in State.ready_states():
                    TaskFileUtils.advance_task_state(task.id)
        else: 
            skills = self.skill_selector.select(prompt)
        for skill in skills:
            self._add_skill(skill)

        self.template = self.loadPrompt()

    def log(self, task_id: str, input: str, output: str):
        log = AgentLog(
            agent=self.agentName, input=input, output=output, timestamp=datetime.now().isoformat()
        )
        TaskFileUtils.append_log_to_task(task_id, log)

    def loadPrompt(self) -> str:
        if not hasattr(self, "_template"):
            try:
                current_dir = os.path.dirname(os.path.abspath(__file__))

                prompt_path = os.path.join(
                    current_dir,
                    "agentPrompts",
                    f"{self.name}.md"
                )

                logger.debug(
                    "Loading prompt for agent '%s' from '%s'",
                    self.name,
                    prompt_path
                )

                if not os.path.exists(prompt_path):
                    raise FileNotFoundError(
                        f"Prompt file not found: {prompt_path}"
                    )

                with open(prompt_path, "r", encoding="utf-8") as file:
                    content = file.read()

                if not content.strip():
                    raise ValueError(
                        f"Prompt file is empty: {prompt_path}"
                    )

                self._template = content

                logger.info(
                    "Loaded prompt for agent '%s' (%d characters)",
                    self.name,
                    len(content)
                )

                return self._template

            except FileNotFoundError as e:
                logger.error(
                    "Missing prompt for agent '%s': %s",
                    self.name,
                    e
                )
                raise

            except UnicodeDecodeError as e:
                logger.error(
                    "Encoding error reading prompt for agent '%s': %s",
                    self.name,
                    e
                )
                raise

            except PermissionError as e:
                logger.error(
                    "Permission denied reading prompt for agent '%s': %s",
                    self.name,
                    e
                )
                raise

            except Exception as e:
                logger.exception(
                    "Unexpected error loading prompt for agent '%s'",
                    self.name
                )
                raise

        return self._template
    
    def build_prompt(self, task: Task | PlanStep | None) -> str:
        # print("---- Build prompt -----")
        sharedAgentSystemPrompt = self.loadSharedAgentSystemPrompt()
        sharedAgentSystemPrompt = sharedAgentSystemPrompt \
            .replace("{{TOOLS}}", self.format_tools(self.tools)) \
            .replace("{{SKILLS}}", self.format_skills(self.skills)) \
            .replace("{{skill_count_limit}}", str(self.skill_count_limit)) \
            .replace("{{SKILL_INFO}}", self.format_skill_options(self.skill_selector.list_skills())) \
            .replace("{{MAX_STEPS}}", str(self.max_steps)) \

        prompt = self.template
        # print(f"Agent baseprompt tokens: {self.count_tokens(prompt, self.llm.model)}")
        if isinstance(task, PlanStep):
            # print("found instance of PlanStep")
            prompt = prompt.replace("{{TASK}}", self.format_planstep(task))
            sharedAgentSystemPrompt = sharedAgentSystemPrompt.replace("{{CURRENT_TASK}}", self.get_current_goal(task))
        elif isinstance(task, Task):
            # print("found instance of Task")
            prompt = prompt.replace("{{TASK}}", self.format_task(task))
            sharedAgentSystemPrompt = sharedAgentSystemPrompt.replace("{{CURRENT_TASK}}", self.get_current_goal(task))
        
        
            
        # print(f"Full prompt tokens: {self.count_tokens(prompt, self.llm.model)}")
        # print(f"sharedAgentSystemPrompt tokens: {self.count_tokens(sharedAgentSystemPrompt, self.llm.model)}")

        prompt = sharedAgentSystemPrompt.replace("{{AGENT_PROMPT}}", prompt)
        # prompt = prompt.replace("{{SHARED_AGENT_SYSTEM_PROMPT}}", sharedAgentSystemPrompt)
        # print(f"Final prompt tokens: {self.count_tokens(prompt, self.llm.model)}")

        # print("----- Agent has access to the following tools: -----  \n")
        # for tool in self.tools.values():
        #     print(f"- {tool.name}")
        # print("----- END ----- \n")

        # print("----- Agent has access to the following skills: ----- \n")
        # for skill in self.skills:
        #     print(f"- {skill.name}")
        # print("----- END ----- \n")

        # self.debug_prints()

        # print("---- Build prompt END ----- \n\n")
        return prompt

    def debug_prints(self):
        print("----- Agent: -----  \n")
        print(f"- {self.name} \n\n")

        print("----- Agent has access to the following tools: -----  \n")
        for tool in self.tools.values():
            print(f"- {tool.name}")
        print("----- END ----- \n\n")

        print("----- Agent has access to the following skills: ----- \n")
        for skill in self.skills:
            print(f"- {skill.name}")
        print("----- END ----- \n\n")


    def count_tokens(self, text: str, model: str = "gpt-4o-mini") -> int:
        encoding = tiktoken.get_encoding("cl100k_base")
        # encoding = tiktoken.encoding_for_model(model)
        tokens = encoding.encode(text)
        return len(tokens)

    def loadSharedAgentSystemPrompt(self) -> str:
        # if not hasattr(self, "_load_skill_prompt"):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        skill_prompt_path = os.path.join(current_dir, "agentPrompts", "shared_agent_system_prompt.md")
        output_rules_path = os.path.join(current_dir, "agentPrompts", "base_prompts", "output_rules.md")
        skill_usage_path = os.path.join(current_dir, "agentPrompts", "base_prompts", "skill_usage.md")
        task_workflow_path = os.path.join(current_dir, "agentPrompts", "base_prompts", "Task_workflow.md")

        with open(skill_prompt_path, "r", encoding="utf-8") as f:
            load_skill_prompt = f.read()
        with open(output_rules_path, "r", encoding="utf-8") as f:
            output_rules = f.read()
        
        with open(task_workflow_path, "r", encoding="utf-8") as f:
            task_workflow = f.read()

        shared_prompt: str = load_skill_prompt \
            .replace("{{OUTPUT_RULES}}", output_rules) \
            .replace("{{TASK_WORKFLOW}}", task_workflow) \
            .replace("{{TASK_TAGS}}", ToolTag.TASKS.value)

        can_load_skills = ToolCapability.LOAD_SKILL in self.allowed_capabilities and ToolCapability.LOAD_SKILL not in self.denied_capabilities
        print(f"SOURCE: loadSharedAgentSystemPrompt: Can load skills: {can_load_skills}")
        skills = " | ".join([f"{skill.name}" for skill in self.skills])
        print(f"Agent has the following skills: \n {skills}")
        
        if can_load_skills:
            with open(skill_usage_path, "r", encoding="utf-8") as f:
                skill_usage = f.read()
            shared_prompt = shared_prompt.replace("{{SKILL_USAGE}}", skill_usage)
        else:
            shared_prompt = shared_prompt.replace("{{SKILL_USAGE}}", "Skills can no longer be loaded \n")

        if self.goal_checker_tools:
            shared_prompt = shared_prompt.replace("{{GOAL_CHECKER_TOOLS}}", self.format_goal_checker_tools())
        else: 
            shared_prompt = shared_prompt.replace("{{GOAL_CHECKER_TOOLS}}", "")

        if self.final_goal:
            shared_prompt = shared_prompt.replace("{{FINAL GOAL}}", self.final_goal)
        else:
            raise ValueError(f"Prompt is missing for agent {self.name}. cannot loadsharedAgentSystemsPrompt")
            
            # self._load_skill_prompt = shared_prompt
        # print(f"Shared prompt tokens: {self.count_tokens(self._load_skill_prompt, self.llm.model)}")
        return shared_prompt

    def format_planstep(self, planStep: PlanStep):
        planstep_formatted_to_prompt = planStep.to_prompt()
        # print(f"PlanStep tokens: {self.count_tokens(planstep_formatted_to_prompt, self.llm.model)}")
        return planstep_formatted_to_prompt

    def format_task(self, task: Task):
        task_formatted_to_prompt = task.to_prompt(self.agentName)
        # print(f"Task tokens: {self.count_tokens(task_formatted_to_prompt, self.llm.model)}")
        return task_formatted_to_prompt

    def format_tools(self, tools: dict):
        tool_formatted_to_prompt = "\n".join([tool.format_for_llm() for tool in tools.values()])
        # print(f"Tools tokens: {self.count_tokens(tool_formatted_to_prompt, self.llm.model)}")
        return tool_formatted_to_prompt

    def format_skills(self, skills: list[SkillNode]):
        skills_formatted_to_prompt = "\n\n".join([f"## Skill: {skill.name}\n{skill.load(True)}" for skill in skills])
        # print(f"skills tokens: {self.count_tokens(skills_formatted_to_prompt, self.llm.model)}")
        return skills_formatted_to_prompt

    def format_goal_checker_tools(self):
        formatted_output = " and ".join(
            f"`{tool.name}`" if hasattr(tool, "name") else f"`{tool.__name__}`" 
            for tool in self.goal_checker_tools
        )
        return formatted_output


    def format_skill_options(self, skill_node: list[SkillNode]):
        
        for skill in self.skills:
            self.skill_name_added.add(skill.name)

        all_allowed_names: set[str] = set()
        all_allowed_keywords: set[str] = set()
        for node in skill_node:
            if node.name not in self.skill_name_added and not any(keyword in self.skill_keywords_added for keyword in node.keywords):
                all_allowed_names.add(node.name)
                all_allowed_keywords.update(node.keywords)
        keywords = " | ".join(sorted(all_allowed_keywords))
        names = " | ".join(sorted(all_allowed_names))
        # print(f"skill options tokens: {self.count_tokens(paths, self.llm.model)}")
        return (
            f"skill_names options for the LoadSkillTool: \n"
            f"{names} \n"
            f"skill_keywords options for the LoadSkillTool: \n"
            f"{keywords}"
            "\n\n"
        )

    def ReActObs(self, prompt: str, max_steps: int) -> AgentResponse:
        observations = []
        loaded_skills = []
        for _ in range(max_steps):
            full_prompt = (
                prompt
                + "\n\nLoaded Skills:\n"
                + "\n\n".join(loaded_skills)
                + "\n\nObservations:\n"
                + self.convert_list_to_string(observations)
            )
            response = self.llm.call(full_prompt)
            parsed = AgentResponse.model_validate_json(response)
            parsedAction: AgentAction = AgentAction.from_string(parsed.action) 
            if parsed and parsedAction == AgentAction.Tool and parsed.tool_name:
                tool = self.tools.get(parsed.tool_name)
                result = self._execute_tool(parsed, tool)

                if parsed.tool_name == "LoadSkillTool":
                    if len(loaded_skills) >= self.skill_count_limit:
                        raise Exception("Skill load limit exceeded")

                    loaded_skills.append(result)

                observations.append({"tool": parsed.tool_name, "result": result})
            elif parsed.action == "final":
                return parsed

        raise Exception("ReAct did not finish in max_steps")

    def ReActObs_stream(self, task: Task | None, planStep: PlanStep | None = None) -> AgentResponse | None:
        tool_executions: list[str] = []
        run_time_prompt_injections: list[str] = []
        final_response: list[tuple[AgentResponse, int, bool, str]] = [] #Agent response, step number, success, code output/tool output

        for _ in range(self.max_steps):            
            if not self._template:
                raise Exception(f"{self.agentName.name} Agent have no loaded template prompt") 
            step: int = _ + 1

            if (step >= self.max_steps - 3 or len(self.skills) > self.skill_count_limit) and any(name == "LoadSkillTool" for name in self.tools.keys()):
                print("Agent can no longer load skills")
                self.__disable_skills([ToolCapability.LOAD_SKILL], [ToolTag.SKILLS])

            if task and isinstance(task, Task):
                task = self._reload_task(task.id)
                if planStep and isinstance(planStep, PlanStep):
                    planStep = self._reload_planStep(task.id, planStep.id)
                    prompt = self.build_prompt(planStep).replace("{{STEP}} ", f"{str(step)} ")
                else:
                    prompt = self.build_prompt(task).replace("{{STEP}} ", f"{str(step)} ")
            else:
                prompt = self.build_prompt(None).replace("{{STEP}} ", f"{str(step)} ")

            print (f"Step {step} of {self.max_steps}")

            run_time_additions = (
                "\n\nObservations:\n"
                + self.convert_list_to_string(tool_executions)
                + "\n\Additional notes:\n"
                + self.convert_list_to_string(run_time_prompt_injections)
            )
            if self.validation_error:
                run_time_additions += (
                    "\n\nThe agent failed to complete the assignment with the following remarks:\n"
                    + self.validation_error
                )
            full_prompt = prompt.replace("{{CONTEXT_AND_STATE}}", run_time_additions)
            token_count = self.count_tokens(full_prompt, self.llm.model)

            print(f"full_prompt tokens: {token_count}")

            # Clear executions between steps
            # tool_executions = []

            if(_ == self.max_steps - 1):
                print("Final Round")
                run_time_prompt_injections.append("This is the last round. Be sure to complete the task and resolve with a final response.")

            # stream tokens
            buffer = ""
            for token in self.llm.stream(full_prompt):
                print(token, end="", flush=True)
                buffer += token

            cleaned_buffer = self._clean_and_parse_json(buffer) 
            try:
                parsed = AgentResponse.model_validate_json(cleaned_buffer)
            except Exception as e:
                print(f"Invalid response output for: {parsed.input}. Be sure to comply with constraints. \n Error: {e}")
                run_time_prompt_injections.append(f"Invalid response output for: {parsed.input}. Be sure to comply with constraints. \n Error: {e}")
                print("Error parsing response: ", e)
                logger.exception(
                    "\n json parsing failed \n %s \n",
                    cleaned_buffer
                )
                logger.exception(
                    "exception '%s'",
                    e
                )
                # raise

            parsedAction: AgentAction = AgentAction.from_string(parsed.action) 
            if parsed and parsedAction == AgentAction.Tool and parsed.tool_name:

                tool = self.tools.get(parsed.tool_name)
                if not tool:
                    print("The tool does not exist")
                    logger.error(
                        f"\n Tool '{parsed.tool_name}' not found \n",
                    )
                    final_response.append((parsed, step, False, f"Tool '{parsed.tool_name}' not found \n"))
                    run_time_prompt_injections.append("The tool does not exist \n")
                    continue

                if parsed.input is None:
                    print("Tool called, but parsed.input is None")
                    run_time_prompt_injections.append("when running a tool, you must provide an input - atleast an empty json object. \n")
                    final_response.append((parsed, step, False, f"Tool called, but parsed.input is None\n"))
                    continue

                if ToolTag.TASKS in tool.tags:
                    prompt_taskid = parsed.input.get("task_id")
                    if prompt_taskid and isinstance(prompt_taskid, str) and not self.is_valid_uuid(prompt_taskid) and task:
                        parsed.input["task_id"] = task.id

                    tool_requires_agent_name = "agent_name" in tool.input_model.model_fields
                    if tool_requires_agent_name:
                        parsed.input["agent_name"] = self.name

                result = self._execute_tool(parsed, tool)

                if result and result.data and result.data.success == False:
                    run_time_prompt_injections.append(f"Tool [{tool.name}] executed, but failed to resolve. Error: {result.data.message} \n")

                if result and not result.data and result.error:
                    run_time_prompt_injections.append(f"Tool [{tool.name}] failed: {result.error} \n")

                if result.data:
                    tool_executions.append(result.to_string())
                    final_response.append((parsed, step, result.data.success, result.to_string()))
                    print(f"Tool output:\n{result.data.to_string()} \n")
                else: 
                    final_response.append((parsed, step, False, result.to_string()))
                    run_time_prompt_injections.append(f"Tool {parsed.tool_name}: failed with no explanation \n")

                if parsed.tool_name == "LoadSkillTool" and isinstance(result.data, LoadSkillOutput):
                    if result and result.data and result.data.skill_nodes:
                        self._add_skills(result.data.skill_nodes, result.data.skill_keywords)
                
            elif parsed.action == "final":
                final_response.append((parsed, step, True, "Agent has completed the task with a final response."))
                self.__print_runtimeOutput(final_response)
                return parsed

        self.__print_runtimeOutput(final_response)
        print("ReAct did not finish")
        return None

    def __print_runtimeOutput(self, final_response: list[tuple[AgentResponse, int, bool, str]]) -> None:
        print("\n\n----- Final Response Summary -----\n")
        # self.debug_prints()
        for response, step, success, output in final_response:
            status = "Success" if success else "Failure"
            print(
                f"- Step: {step}\n"
                f"- Tool: {response.tool_name} | status: {status} | output: {output} \n"
                f"- Input:\n {response.to_string()} \n\n"
            )

        # self.debug_prints()
        print("----- End of Summary -----\n\n")

    def __disable_skills(self, toolCapabilities: list[ToolCapability] | None, tooltags: list[ToolTag] | None) -> None:
        if toolCapabilities:
            for capability in toolCapabilities:
                if capability not in self.denied_capabilities:
                    self.denied_capabilities.append(capability)
                    print(f"Disabling capability: {capability}")
                else:
                    print(f"Capability {capability} already disabled.")

                if capability in self.allowed_capabilities:
                    self.allowed_capabilities = [c for c in self.allowed_capabilities if c != capability]
                    print(f"Removing all instances of capability from allowed: {capability}")
                    
        if tooltags:
            for tag in tooltags:
                if tag in self.allowed_tags:
                    self.allowed_tags = [t for t in self.allowed_tags if t != tag]
                    print(f"Disabling tag: {tag}")
                else:
                    print(f"Tag {tag} already disabled or not present.")

        self.tools = self.tool_selector.select(self)

        # print(f"Current allowed capabilities:\n")
        # for capability in self.allowed_capabilities:
        #     print(f"- {capability}")
        # print(f"\nCurrent denied capabilities:\n")
        # for capability in self.denied_capabilities:
        #     print(f"- {capability}")
        # print(f"\nCurrent allowed tags:\n")
        # for tag in self.allowed_tags:
        #     print(f"- {tag}")



    def is_valid_uuid(self, val: str) -> bool:
        try:
            return bool(uuid.UUID(str(val)))
        except (ValueError, TypeError, AttributeError):
            return False

    def _add_skills(self, skillNodes: list[SkillNode] | None, skill_tags: list[str] | None = None) -> None:
        if skillNodes and skill_tags:
            for skill_node in skillNodes:
                self._add_skill(skill_node)
            for skill_tag in skill_tags:
                self._add_skill(None, skill_tag)

    def _add_skill(self, skillNode: SkillNode | None, skill_tag: str | None = None) -> None:
        if skillNode and skillNode.name:
            if skillNode.name not in self.skill_name_added:
                self.skills.append(skillNode)
                self.skill_name_added.add(skillNode.name)
                print(f"Adding {skillNode.name} to the skill list.")
            else: 
                print(f"Skill {skillNode.name} already added.")
        elif skill_tag and isinstance(skill_tag, str):
            if skill_tag not in self.skill_keywords_added:
                self.skill_keywords_added.add(skill_tag)
        else:
            print(f"Skill node or skill tag is None. \n")
   
    def _clean_and_parse_json(self, raw_string: str) -> str:
        """Cleans up markdown and Python dict formats, returning a strict JSON string."""
        if not isinstance(raw_string, str):
            return raw_string
        
        cleaned = raw_string.strip()
        match = re.match(r"^```(?:json|JSON)?\s*(.*?)\s*```\$", cleaned, re.DOTALL)
        if match:
            cleaned = match.group(1).strip()
        else:
            cleaned = (
                cleaned.replace("```json", "")
                .replace("```JSON", "")
                .replace("```", "")
                .strip()
            )

        try:
            json.loads(cleaned)
            return cleaned
        except json.JSONDecodeError:
            pass

        try:
            python_obj = ast.literal_eval(cleaned)
            return json.dumps(python_obj, ensure_ascii=False)
        except (ValueError, SyntaxError):
            return cleaned

    def convert_list_to_string(self, obs: list[str]) -> str:
        return "\n\n".join(obs)

    def run(self, task: Task | str) -> Task:
        raise NotImplementedError("Subclasses must implement this method")

    def get_current_goal(self, task: Task | PlanStep | str) -> str:
        raise NotImplementedError("Subclasses must implement this method")

    def _execute_tool(self, parsed: AgentResponse, tool: Tool[Any, Any] | None) -> ToolResult[ToolOutput]:

        if not tool:
            raise Exception(f"Tool not found: {parsed.tool_name}")

        input_data = parsed.input if parsed.input is not None else {}
        if not isinstance(input_data, dict):
            raise Exception("Tool input must be a dictionary")

        return tool.__call__(input_data)

    def _reload_task(self, task_id: str) -> Task:
        task = TaskFileUtils.load_task(task_id)
        return task

    def _reload_planStep(self, task_id: str, planStep_id: str) -> PlanStep:
        planStep = TaskFileUtils.load_planstep(task_id, planStep_id)
        return planStep
