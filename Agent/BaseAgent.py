from datetime import datetime
from Agent.AgentResponse import AgentResponse
from Agent.AgentNames import AgentName
from Skills.skill_utils.SkillNode import SkillNode
from Skills.skill_utils.SkillSelector import SkillSelector
from Tasks.Task import Task, AgentLog, PlanStep
from Tools.tool_utils.ToolSelector import ToolSelector

class BaseAgent:
    def __init__(self, name: AgentName, llm, tool_selector: ToolSelector, skill_selector: SkillSelector):
        self.name = name.value
        self.agentName = name
        self.llm = llm
        self.tool_selector = tool_selector
        self.skill_selector = skill_selector
        self.template = self.loadPrompt()
        self.skill_count_limit = 3 # Number of skills an agent can load while running

    def prepare(self, task: Task):
        self.tools = self.tool_selector.select(self.agentName)
        self.skills = self.skill_selector.select(task)
        self.template = self.loadPrompt()

    def log(self, task: Task, input: str, output: str):
        task.logs.append(AgentLog(
            agent=self.name,
            input=input,
            output=output,
            timestamp=datetime.now().isoformat()
        ))

    def loadPrompt(self):
        if not hasattr(self, "_template"):
            with open(f"agentPrompts/{self.name}.md") as f:
                self._template = f.read()
        return self._template
        
    def build_prompt(self, task: Task):
        return self.combine_prompt(
            self.template,
            task,
            self.tools,
            self.skills
        )
    
    def build_prompt_from_planstep(self, planStep: PlanStep):
        return self.combine_prompt_from_planstep(
            self.template,
            planStep,
            self.tools,
            self.skills
        )
    
    def combine_prompt(self, template, task: Task, tools, skills):
        return template \
            .replace("{{TASK}}", self.format_task(task)) \
            .replace("{{TOOLS}}", self.format_tools(tools)) \
            .replace("{{SKILLS}}", self.format_skills(skills)) \
            .replace("{{Load_skill}}", self.loadSkillSystemPrompt())
    
    def combine_prompt_from_planstep(self, template, planStep: PlanStep, tools, skills):
        return template \
            .replace("{{TASK}}", self.format_planstep(planStep)) \
            .replace("{{TOOLS}}", self.format_tools(tools)) \
            .replace("{{SKILLS}}", self.format_skills(skills)) \
            .replace("{{Load_skill}}", self.loadSkillSystemPrompt())
    
    def loadSkillSystemPrompt(self):
        if not hasattr(self, "_load_skill_prompt"):
            with open("agentPrompts/Load_skill.md") as f:
                content = f.read()
                content = content.replace(
                    "{{skill_count_limit}}",
                    str(self.skill_count_limit)
                )
                self._load_skill_prompt = content
        return self._load_skill_prompt
    
    def format_task(self, task: Task):
        return f"Title: {task.title}\nDescription: {task.description}"
    
    def format_planstep(self, planStep: PlanStep):
        return f"Description: {planStep.description}"

    def format_tools(self, tools: dict):
        return "\n\n".join([
            tool.format_to_json()
            for tool in tools.values()
        ])

    def format_skills(self, skills: list):
        return "\n\n".join([
            f"## Skill: {skill.name}\n{skill.load()}"
            for skill in skills
        ])
    
    def format_skill_tree(self, tree: SkillNode) -> str:
        def recurse(node, indent=0):
            s = "  " * indent + f"- {node.name}\n"
            for child in node.children:
                s += recurse(child, indent + 1)
            return s

        return recurse(tree)
    
    def ReActObs(self, prompt: str, max_steps: int) -> AgentResponse:
        observations = []
        loaded_skills = []
        for _ in range(max_steps):
            full_prompt = (
                prompt
                + "\n\nLoaded Skills:\n"
                + "\n\n".join(loaded_skills)
                + "\n\nObservations:\n"
                + self.render_observations(observations)
            )
            response = self.llm(full_prompt)
            parsed = AgentResponse.model_validate_json(response)
            if parsed and parsed.action == "tool" and parsed.tool_name:
                tool = self.tools.get(parsed.tool_name)

                if not tool:
                    raise Exception(f"Tool not found: {parsed.tool_name}")

                if not isinstance(parsed.input, dict):
                    raise Exception("Tool input must be a dictionary")

                if not parsed.input:
                    raise Exception(f"Tool {parsed.tool_name} called without input")

                if not hasattr(tool, "input_model"):
                    raise Exception(f"Tool {parsed.tool_name} missing input_model")

                try:
                    validated = tool.input_model(**parsed.input)
                except Exception as e:
                    raise Exception(f"Invalid input for tool {parsed.tool_name}: {e}")

                result = tool.run(validated)

                if parsed.tool_name == "load_skill":
                    if len(loaded_skills) >= self.skill_count_limit:
                        raise Exception("Skill load limit exceeded")

                    loaded_skills.append(result)

                observations.append({
                    "tool": parsed.tool_name,
                    "result": result
                })
            elif parsed.action == "final":
                return parsed
            
        raise Exception("ReAct did not finish in max_steps")
    
    def render_observations(self, obs: list[dict]) -> str:
        return "\n\n".join(
            f"[{o['tool']}]\n{o['result']}"
            for o in obs
        )
    
    def run(self, task: Task) -> Task:
        raise NotImplementedError("Subclasses must implement this method")