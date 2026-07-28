import ast
from datetime import datetime
import json
import os
import re
from typing import Any, Dict
from Agent.AgentResponse import AgentAction, AgentResponse
from Agent.AgentNames import AgentName
from LLM.LLM import LLM
from Skills.skill_utils.SkillNode import SkillNode
from Skills.skill_utils.SkillSelector import SkillSelector
from Tasks.Task import Task, AgentLog, PlanStep
from Tools.LoadSkillTool import LoadSkillOutput, LoadSkillTool
from Tools.Tool import Tool, ToolException, ToolOutput, ToolResult
from Tools.tool_utils.ToolCapability import ToolCapability
from Tools.tool_utils.ToolTag import ToolTag
import tiktoken

from Tools.tool_utils.ToolSelector import ToolSelector
import logging


logger = logging.getLogger(__name__)
class BaseAgent:
    DEFAULT_ALLOWED_TAGS = [ToolTag.TASKS, ToolTag.UTILITY, ToolTag.SKILLS]
    DEFAULT_ALLOWED_CAPABILITIES = [ToolCapability.READ_TASKS, ToolCapability.UPDATE_TASKS, ToolCapability.VALIDATE_TASKS, ToolCapability.LOAD_SKILL]
    
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
        self.denied_capabilities: list[str] = []
        self.tools: Dict[str, Tool] = {}
        self.skill_name_added: set[str] = set()
        self.skill_tags_added: set[str] = set()
        self.skills: list[SkillNode] = []
        self.max_steps = 15
        
    def prepare(self, task: Task | str):
        self.tools = self.tool_selector.select(self)
        skills = self.skill_selector.select(task)
        for skill in skills:
            self._add_skill(skill)

        self.template = self.loadPrompt()

    def log(self, task: Task, input: str, output: str):
        task.logs.append(
            AgentLog(
                agent=self.agentName, input=input, output=output, timestamp=datetime.now().isoformat()
            )
        )

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
        print("---- Build prompt -----")
        sharedAgentSystemPrompt = self.loadSharedAgentSystemPrompt()
        sharedAgentSystemPrompt = sharedAgentSystemPrompt \
            .replace("{{TOOLS}}", self.format_tools(self.tools)) \
            .replace("{{SKILLS}}", self.format_skills(self.skills)) \
            .replace("{{skill_count_limit}}", str(self.skill_count_limit)) \
            .replace("{{SKILL_INFO}}", self.format_skill_options(self.skill_selector.list_skills())) \
            .replace("{{MAX_STEPS}}", str(self.max_steps)) \

        prompt = self.template
        # print(f"Agent baseprompt tokens: {self.count_tokens(prompt, self.llm.model)}")
        if isinstance(task, Task):
            print("found instance of Task")
            prompt = prompt.replace("{{TASK}}", self.format_task(task))
        if isinstance(task, PlanStep):
            print("found instance of PlanStep")
            prompt = prompt.replace("{{TASK}}", self.format_planstep(task))
            
        # print(f"Full prompt tokens: {self.count_tokens(prompt, self.llm.model)}")
        # print(f"sharedAgentSystemPrompt tokens: {self.count_tokens(sharedAgentSystemPrompt, self.llm.model)}")

        prompt = sharedAgentSystemPrompt.replace("{{AGENT_PROMPT}}", prompt)
        # prompt = prompt.replace("{{SHARED_AGENT_SYSTEM_PROMPT}}", sharedAgentSystemPrompt)
        print(f"Final prompt tokens: {self.count_tokens(prompt, self.llm.model)}")

        print("----- Agent has access to the following tools: -----  \n")
        for tool in self.tools.values():
            print(f"- {tool.name}")
        print("----- END ----- \n")

        print("----- Agent has access to the following skills: ----- \n")
        for skill in self.skills:
            print(f"- {skill.name}")
        print("----- END ----- \n")

        print("---- Build prompt END ----- \n\n")
        return prompt

    def count_tokens(self, text: str, model: str = "gpt-4o-mini") -> int:
        encoding = tiktoken.get_encoding("cl100k_base")
        # encoding = tiktoken.encoding_for_model(model)
        tokens = encoding.encode(text)
        return len(tokens)

    def loadSharedAgentSystemPrompt(self) -> str:
        if not hasattr(self, "_load_skill_prompt"):
            current_dir = os.path.dirname(os.path.abspath(__file__))
            
            skill_prompt_path = os.path.join(current_dir, "agentPrompts", "shared_agent_system_prompt.md")
            output_rules_path = os.path.join(current_dir, "agentPrompts", "base_prompts", "output_rules.md")
            skill_usage_path = os.path.join(current_dir, "agentPrompts", "base_prompts", "skill_usage.md")
            task_workflow_path = os.path.join(current_dir, "agentPrompts", "base_prompts", "Task_workflow.md")

            
            with open(skill_prompt_path, "r", encoding="utf-8") as f:
                load_skill_prompt = f.read()
            with open(output_rules_path, "r", encoding="utf-8") as f:
                output_rules = f.read()
            with open(skill_usage_path, "r", encoding="utf-8") as f:
                skill_usage = f.read()
            with open(task_workflow_path, "r", encoding="utf-8") as f:
                task_workflow = f.read()

            shared_prompt = load_skill_prompt \
                .replace("{{OUTPUT_RULES}}", output_rules) \
                .replace("{{TASK_WORKFLOW}}", task_workflow) \
                .replace("{{TASK_TAGS}}", ToolTag.TASKS.value)

            # .replace("{{SKILL_USAGE}}", skill_usage) \
                # <AVAILABLE_SKILLS>
                # {{SKILLS}}
                # <AVAILABLE_SKILLS>


            
            self._load_skill_prompt = shared_prompt
        # print(f"Shared prompt tokens: {self.count_tokens(self._load_skill_prompt, self.llm.model)}")
        return self._load_skill_prompt

    def format_planstep(self, planStep: PlanStep):
        planstep_formatted_to_prompt = planStep.to_prompt()
        # print(f"PlanStep tokens: {self.count_tokens(planstep_formatted_to_prompt, self.llm.model)}")
        return planstep_formatted_to_prompt

    def format_task(self, task: Task):
        task_formatted_to_prompt = task.to_prompt(self.agentName)
        # print(f"Task tokens: {self.count_tokens(task_formatted_to_prompt, self.llm.model)}")
        return task_formatted_to_prompt

    def format_tools(self, tools: dict):
        tool_formatted_to_prompt = "\n\n".join([tool.format_for_llm() for tool in tools.values()])
        # print(f"Tools tokens: {self.count_tokens(tool_formatted_to_prompt, self.llm.model)}")
        return tool_formatted_to_prompt

    def format_skills(self, skills: list[SkillNode]):
        skills_formatted_to_prompt = "\n\n".join([f"## Skill: {skill.name}\n{skill.load(True)}" for skill in skills])
        # print(f"skills tokens: {self.count_tokens(skills_formatted_to_prompt, self.llm.model)}")
        return skills_formatted_to_prompt

    def format_skill_options(self, skill_node: list[SkillNode]):
        for skill in self.skills:
            self.skill_name_added.add(skill.name)

        summaries = []
        for node in skill_node:
            if node.name not in self.skill_name_added:
                summaries.append(
                    f"- name: {node.name}\n"
                    f"- Keywords: {node.keywords}\n\n"
                )
        # paths = f"AVAILABLE SKILLS:\n\n {summaries}"
        # print(f"skill options tokens: {self.count_tokens(paths, self.llm.model)}")
        return f"AVAILABLE SKILLS:\n\n {summaries}"

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

    def ReActObs_stream(self):
        tool_executions: list[str] = []
        run_time_prompt_injections: list[str] = []

        for _ in range(self.max_steps):            
            if not self._template:
                raise Exception(f"{self.agentName.name} Agent have no loaded template prompt") 

            prompt = self.build_prompt(None)
            print (f"Step {_+1} of {self.max_steps}")
            prompt.replace("{{STEP}} ", f"{_+1} ")

            run_time_additions = (
                "\n\nObservations:\n"
                + self.convert_list_to_string(tool_executions)
                + "\n\Additional notes:\n"
                + self.convert_list_to_string(run_time_prompt_injections)
            )
            full_prompt = prompt.replace("{{CONTEXT_AND_STATE}}", run_time_additions)
            token_count = self.count_tokens(full_prompt, self.llm.model)

            print(f"full_prompt tokens: {token_count}")

            # Clear the buffer after each iteration
            # run_time_prompt_injections = []
            tool_executions = []

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
                print("Error parsing response: ", e)
                logger.exception(
                    "\n json parsing failed \n %s \n",
                    cleaned_buffer
                )
                logger.exception(
                    "exception '%s'",
                    e
                )
                raise

            parsedAction: AgentAction = AgentAction.from_string(parsed.action) 
            if parsed and parsedAction == AgentAction.Tool and parsed.tool_name:
                tool = self.tools.get(parsed.tool_name)
                if not tool:
                    print("The tool does not exist")
                    logger.error(
                        "\n Tool '%s' not found \n",
                    )
                    run_time_prompt_injections.append("The tool does not exist \n")
                    continue

                result = self._execute_tool(parsed, tool)
                
                if parsed.tool_name == "LoadSkillTool" and isinstance(result.data, LoadSkillOutput):
                    print(1)
                    if result and result.data:
                        if result.data.skill_nodes:
                            self._add_skills(result.data.skill_nodes, result.data.skill_keywords)
                        else:
                            run_time_prompt_injections.append("\n No skill nodes found for the loaded skill. \n")
                 
                    if len(self.skills) > self.skill_count_limit:
                        run_time_prompt_injections.append(f"\n Skills loaded exceed limit of: {self.skill_count_limit}. No more skills can be loaded \n")

                if result.data:
                    tool_executions.append(result.to_string())
                    if(result.data.success is True):
                        print(f"Tool {parsed.tool_name}: executed successfully. \n")
                    else:
                        print(f"Failed to execute tool {parsed.tool_name}. \n")
                    print(f"Tool output:\n  {result.data.to_string()} \n")
                else: 
                    run_time_prompt_injections.append(f"Tool {parsed.tool_name}: failed with no explanation \n")

            elif parsed.action == "final":
                return parsed

        raise Exception("ReAct did not finish")

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
                print(f"Adding {skillNode.name} to the skill list. \n")
            else: 
                print(f"Skill {skillNode.name} already added. \n")
        elif skill_tag and isinstance(skill_tag, str):
            if skill_tag not in self.skill_tags_added:
                self.skill_tags_added.add(skill_tag)
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

    def _execute_tool(self, parsed: AgentResponse, tool: Tool[Any, Any] | None) -> ToolResult[ToolOutput]:

        if not tool:
            raise Exception(f"Tool not found: {parsed.tool_name}")

        input_data = parsed.input if parsed.input is not None else {}
        if not isinstance(input_data, dict):
            raise Exception("Tool input must be a dictionary")

        # try:
        #     validated_input = tool.input_model(**input_data)
        # except Exception as e:
        #     raise Exception(f"Failed to validate arguments for {tool.name}: {e}")

        return tool.__call__(input_data)
