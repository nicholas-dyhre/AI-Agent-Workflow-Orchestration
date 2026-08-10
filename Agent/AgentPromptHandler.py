import collections
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List
from Agent.AgentNames import AgentName
from Agent.AgentResponse import AgentResponse
from Agent.Utils import Utils
from Skills.skill_utils.SkillNode import SkillNode
from Tools.Tool import Tool, ToolResult
from Common.color_printer import error, wild

@dataclass
class PromptInput:
    tools: Dict[str, Tool]
    skills: List[SkillNode]
    allowed_skills: list[SkillNode]
    skill_limit: int
    tool_executions: list[tuple[ToolResult, int, AgentResponse]]
    step: int
    run_time_prompt_injections: str

@dataclass
class CommandRunOutput:
    args: str | list[str]
    stderr: str | None
    stdout: str | None
    returncode: int | None

    def is_success(self) -> bool:
        if self.returncode is None:
            return False
        return self.returncode == 0

class AgentPromptHandler():
    def __init__(self):
        self.agentName: AgentName = AgentName.UNKNOWN
        self.final_goal = ""
        self.current_goal = ""
        self.template = ""
        self.can_load_skills = True
        self.max_steps = 0
        self.agent_prompt_dir: Path = Path.cwd() / "Agent" / "agentPrompts"

    def prepare(self, prompt: str, current_goal: str, max_step: int, agentname: AgentName):
        self.final_goal = prompt
        self.current_goal = current_goal
        self.max_steps = max_step
        self.agentName: AgentName = agentname
        self.template = self.__loadPrompt()

    def build_prompt(self, promptInput: PromptInput) -> str:
        prompt = self.__loadSharedAgentSystemPrompt() \
            .replace("{{TOOLS}}", Utils.format_tools(promptInput.tools)) \
            .replace("{{SKILLS}}", Utils.format_skills(promptInput.skills)) \
            .replace("{{MAX_STEPS}}", str(self.max_steps)) \
            .replace("{{CURRENT_TASK}}", self.current_goal) \
            .replace("{{AGENT_PROMPT}}", self.template) \
            .replace("{{STEP}}", str(promptInput.step)) \

            
        prompt = self.__handle_skill_loader(prompt, promptInput)
        prompt = self.__handle_run_time_injections(prompt, promptInput)

        return prompt

    def __handle_run_time_injections(self, prompt, promptInput: PromptInput) -> str:
        history_length = 3
        threshold = 2

        tool_executions_prompt = "\n".join(
            Utils.to_run_time_executions(tool_result.model_copy(), steps, response.model_copy())
            for tool_result, steps, response in promptInput.tool_executions[-history_length:]
        ) + "\n" + self.__get_tool_warning(promptInput.tool_executions, history_length, threshold)

        run_time_additions = (
            f"### Execution History Log\n"
            f"*State variables are tracked below. Do not repeat failed actions.*\n"
            f"{tool_executions_prompt}"
            f"\n\n### Run time issues:\n"
            f"{promptInput.run_time_prompt_injections}\n"

        )

        full_prompt = prompt.replace("{{CONTEXT_AND_STATE}}", run_time_additions)
        token_count = Utils.count_tokens(full_prompt)
        wild(f"full_prompt tokens: {token_count}")
        return full_prompt

    def __get_tool_warning(self, tool_executions_raw: list[tuple[ToolResult, int, AgentResponse]], history_length: int = 3, threshold: int = 2) -> str:
        history_length = 3
        threshold = 2

        if len(tool_executions_raw) < history_length:
            return ""

        # Get the last 3 execution tuples and count the tool names
        last_executions = tool_executions_raw[-history_length:]
        tool_counts = collections.Counter(response.tool_name for _, _, response in last_executions)

        # Find all tools that met or exceeded the threshold
        offending_tools = [tool for tool, count in tool_counts.items() if count >= threshold and tool]

        if offending_tools:
            tool_names_formatted = " | ".join(offending_tools)
            return (
                f"\nSYSTEM WARNING: You have called '{tool_names_formatted}' multiple times without making progress. "
                f"You are strictly forbidden from calling '{tool_names_formatted}' on this step. Choose a different tool to break the loop.\n"
            )

        return ""

    def __loadPrompt(self) -> str:
        if not hasattr(self, "_template"):
            try:
                name = self.agentName.value
                prompt_path = self.agent_prompt_dir / f"{name}.md"

                if not Path.exists(prompt_path):
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

                return self._template

            except FileNotFoundError as e:
                error(f"Missing prompt for agent '{name}': {e}")
                raise

            except UnicodeDecodeError as e:
                error(f"Encoding error reading prompt for agent '{name}': {e}")
                raise

            except PermissionError as e:
                error(f"Permission denied reading prompt for agent '{name}': {e}")
                raise

            except Exception as e:
                error(f"Unexpected error loading prompt for agent '{name}': {e}")
                raise

        return self._template    
    
    def __loadSharedAgentSystemPrompt(self) -> str:        
        skill_prompt_path = self.agent_prompt_dir / "shared_agent_system_prompt.md"
        output_rules_path = self.agent_prompt_dir / "base_prompts" / "output_rules.md"
        task_workflow_path = self.agent_prompt_dir / "base_prompts" / "Task_workflow.md"

        with open(skill_prompt_path, "r", encoding="utf-8") as f:
            load_skill_prompt = f.read()
        with open(output_rules_path, "r", encoding="utf-8") as f:
            output_rules = f.read()
        with open(task_workflow_path, "r", encoding="utf-8") as f:
            task_workflow = f.read()

        shared_prompt: str = load_skill_prompt \
            .replace("{{OUTPUT_RULES}}", output_rules) \
            .replace("{{TASK_WORKFLOW}}", task_workflow)        

        if self.final_goal:
            shared_prompt = shared_prompt.replace("{{FINAL GOAL}}", self.final_goal)
        else:
            raise ValueError(f"Prompt is missing for agent {self.agentName.value}. cannot loadsharedAgentSystemsPrompt")
            
        return shared_prompt

    def __handle_skill_loader(self, prompt, promptInput: PromptInput) -> str:
        if self.can_load_skills:
            skill_usage_path = self.agent_prompt_dir / "base_prompts" / "skill_usage.md"
            with open(skill_usage_path, "r", encoding="utf-8") as f:
                skill_usage = f.read()
            prompt = prompt\
                .replace("{{SKILL_USAGE}}", skill_usage) \
                .replace("{{SKILL_COUNT_LIMIT}}", str(promptInput.skill_limit)) \
                .replace("{{SKILL_COUNT}}", str(len(promptInput.skills))) \
                .replace("{{SKILL_INFO}}", Utils.format_skill_options(promptInput.allowed_skills)) \
                
        else:
            prompt = prompt.replace("{{SKILL_USAGE}}", "")

        return prompt