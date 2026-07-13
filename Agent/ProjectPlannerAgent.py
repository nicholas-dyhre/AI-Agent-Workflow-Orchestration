from Agent.AgentNames import AgentName
from Agent.BaseAgent import BaseAgent
from Agent.AgentResponse import AgentResponse
from Skills.skill_utils.SkillSelector import SkillSelector
from Tools.tool_utils.ToolSelector import ToolSelector
    
class ProjectPlannerAgent(BaseAgent):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.name = AgentName.PROJECT_PLANNER.value
        self.agentName = AgentName.PROJECT_PLANNER


        self.allowed_tags.extend([
            "filesystem",
            "planning"
        ])


        self.allowed_capabilities.extend([
            "create_tasks",
            "save_tasks"
        ])
        
    def run(self, prompt: str):
        prompt = self._build_prompt()
        self.llm(prompt)
        return prompt

    def _build_prompt(self):
        return self._combine_prompt(
            self.tools,
            self.skills
        )
    
    def _combine_prompt(self, tools, skills):
        return self.template \
            .replace("{{TOOLS}}", self.format_tools(tools)) \
            .replace("{{SKILLS}}", self.format_skills(skills)) \
            .replace("{{Load_skill}}", self.loadSkillSystemPrompt())