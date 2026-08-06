from Agent.AgentNames import AgentName
from Agent.BaseAgent import BaseAgent
from Skills.skill_utils.SkillSelector import SkillSelector
from Tasks.Task import Task
from Tasks.TaskState import State
from Tools.Task.ListTaskTool import ListTasksTool
from Tools.Task.TaskFileUtils import TaskFileUtils
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
        self.allowed_capabilities.extend([ToolCapability.SAVE_TASKS, ToolCapability.MODIFY_TASKS, ToolCapability.READ_TASKS])
        self.denied_capabilities.extend([
            ToolCapability.CREATE_PLAN_STEP, 
            ToolCapability.GIT,
            ToolCapability.CODE,
            ToolCapability.CREATE_PLAN_STEP,
            ToolCapability.CREATE_BRANCH,
            ToolCapability.CREATE_PULL_REQUEST,
            ToolCapability.COMMIT_CHANGES,
            ToolCapability.PUSH_CHANGES,
            ToolCapability.GIT_GET_REPO_INFO,
            ToolCapability.GENERATE_CODE,
            ToolCapability.READ_PLAN_STEPS,
        ])
        self.goal_checker_tools.extend([
            ListTasksTool
        ])

    def run(self, prompt: str):
        self.prepare(prompt)
        self._template = f"# Project description: \n {prompt}" + self._template

        print(f"running {self.name}")
        status = False
        while not status:
            status, validate_result = self.validate_result()
            if not status:
                self.validation_error = validate_result

            self.ReActObs_stream(None)

        return prompt

    def get_current_goal(self, task: str) -> str:
        subgoal = (f"You will create tasks, that when solved, will produce and output that solves: {task} \n")
        existing_tasks, _ = TaskFileUtils.load_all_tasks()
        if existing_tasks:
            tasks_to_string = "\n".join([
                (
                    f"- Task Id: {task.id}\n"
                    f"- Status: {task.status.value}\n"
                    f"- Description: {task.description}\n"
                )
                for task in existing_tasks])

            subgoal += f"There already exists Tasks. Determine if the existing tasks are sufficient. If they can be improved or expanded, do so. Otherwise respond with a final response. {tasks_to_string}"
        print(
            f"Agent: {self.name}"
            f"Current subgoal: {subgoal}"
        )
        return subgoal

    def validate_result(self) -> tuple[bool, str]:
        validation_errors: str = ""

        new_tasks, skipped = TaskFileUtils.load_all_tasks()
        not_completed = [task for task in new_tasks if not task.status in State.completed_states()]

        if not not_completed:
            validation_errors += "Not tasks to validate. All tasks are completed. Likely because no new tasks was created.\n"
        
        status = False if validation_errors else True
        return (status, validation_errors)
