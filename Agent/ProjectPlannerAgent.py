from typing import Generator

from Agent.AgentNames import AgentName
from Agent.BaseAgent import BaseAgent
from Skills.skill_utils.SkillSelector import SkillSelector
from Tools.tool_utils.ToolCapability import ToolCapability
from Tools.tool_utils.ToolSelector import ToolSelector
from LLM.LLM import LLM
from Skills.skill_utils.SkillSelector import SkillSelector
from Tools.tool_utils.ToolSelector import ToolSelector
from Tools.tool_utils.ToolTag import ToolTag

class ProjectPlannerAgent(BaseAgent):
    def __init__(self, llm: LLM, tool_selector: ToolSelector, skill_selector: SkillSelector):
        super().__init__(llm, tool_selector, skill_selector)
        self.name = AgentName.PROJECT_PLANNER.value
        self.agentName = AgentName.PROJECT_PLANNER
        self.allowed_tags.extend([ToolTag.FILESYSTEM, ToolTag.PERSISTENCE])
        self.allowed_capabilities.extend([ToolCapability.SAVE_TASKS, ToolCapability.MODIFY_TASKS])
        self.denied_capabilities.extend(["development"])

    def run(self, prompt: str):
        self.prepare(prompt)
        self._template = f"# Project description: \n {prompt}" + self._template

        print(f"running {self.name}")
        
        # prompt = self.build_prompt(None)


        # res = self.llm.call(prompt)
        # response_stream = self.llm.stream(prompt)
        # self.print_stream(response_stream)
        self.ReActObs_stream()

        # print(f"Agent {self.name} finished. Result {res}")

        print(
    f"""
Agent used:

Tools:
{chr(10).join(f"- {tool.name}" for tool in self.tools.values())}

Skills:
{chr(10).join(f"- {skill.name}" for skill in self.skills)}

Capabilities:
{chr(10).join(f"- {cap}" for cap in self.allowed_capabilities)}

Denied capabilities:
{chr(10).join(f"- {cap}" for cap in self.denied_capabilities)}
"""
)
        return prompt
    
    def print_stream(self, stream: Generator[str, None, None]):
        """
        Prints streaming LLM output as it arrives.
        """
        print("\n🤖 AI Response:\n")

        for chunk in stream:
            print(chunk, end="", flush=True)

        print("\n")
