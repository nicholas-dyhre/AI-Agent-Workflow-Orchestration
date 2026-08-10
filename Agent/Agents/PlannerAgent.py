from Agent.BaseAgent import BaseAgent
from Agent.AgentNames import AgentName
from Tasks.Task import Task
from LLM.LLM import LLM
from Skills.skill_utils.SkillSelector import SkillSelector
from Tasks.TaskState import State
from Tools.Task.ListPlanStepsTool import ListPlanStepsTool
from Tools.tool_utils.ToolCapability import ToolCapability
from Tools.tool_utils.ToolSelector import ToolSelector
from Tools.tool_utils.ToolTag import ToolTag
from Tools.Task.TaskFileUtils import TaskFileUtils


class PlannerAgent(BaseAgent):
    def __init__(self, llm: LLM, tool_selector: ToolSelector, skill_selector: SkillSelector):
        super().__init__(llm, tool_selector, skill_selector)
        self.name = AgentName.PLANNER.value
        self.agentName = AgentName.PLANNER
        self.toolRepository.allowed_tags.extend([ToolTag.TASKS, ToolTag.PERSISTENCE, ToolTag.FILESYSTEM, ToolTag.QUERY])
        self.toolRepository.allowed_capabilities.extend([
            ToolCapability.MODIFY_TASKS, 
            ToolCapability.WRITE_TASK_LOGS, 
            ToolCapability.SAVE_TASKS, 
            ToolCapability.CREATE_PLAN_STEP, 
            ToolCapability.READ_PLAN_STEPS,
            ToolCapability.MODIFY_PLAN_STEP
        ])
        self.toolRepository.denied_capabilities.extend([
            ToolCapability.CREATE_TASK, 
            ToolCapability.GIT,
            ToolCapability.CODE,
            ToolCapability.CREATE_BRANCH,
            ToolCapability.CREATE_PULL_REQUEST,
            ToolCapability.COMMIT_CHANGES,
            ToolCapability.PUSH_CHANGES,
            ToolCapability.GIT_GET_REPO_INFO,
            ToolCapability.GENERATE_CODE,
        ])
        # self.goal_checker_tools.extend([
        #     ListPlanStepsTool
        # ])

    def run(self, task: Task) -> Task:
        if task.plan:
            print(f"Task {task.id} already has a plan. Skipping planning.")
            return task

        if task.plan:
            plan_step_prompt = "\n".join([f"- {step.id}: {step.description}" for step in task.plan])
            prompt_addtion: str = (
                f"\n\nNote: The task already has a plan with {len(task.plan)} steps. Please review, update and improve the plan as necessary."
                f"\n\nCurrent plan steps (id : description):\n"
                + plan_step_prompt
                )
            self.template = f"{self.template}\n{prompt_addtion}"

        status = False
        while status is False:
            patched_task = TaskFileUtils.load_task(task.id)
            self.ReActObs_stream(patched_task)
            status, message = self.validate_result(task)
            if not status:
                self.validation_error = message 
                TaskFileUtils.patch_task(task.id, {"status": State.PLANNING})

        self.log(
            task.id,
            input=task.description,
            output=f"Planner completed execution. Plan now contains {len(patched_task.plan)} steps.",
        )

        if not patched_task.status == State.READY_FOR_DEVELOPMENT:
            TaskFileUtils.patch_task(patched_task.id, {"status" : State.READY_FOR_DEVELOPMENT.value})

        print(f"Planner completed execution. Plan now contains {len(patched_task.plan)} steps.")

        return patched_task

    def get_current_goal(self, task: Task) -> str:
        subgoal = (f"Target task to break down: '{task.description}' \n")
        if task.plan:
            planSteps: str = "\n".join(planStep.to_prompt() for planStep in task.plan)
            subgoal += f"Task already has plansteps. Determine if the steps are sufficient, or if they need to be expanded or corrected. {planSteps}"
        print(
            f"Agent: {self.name}"
            f"Current subgoal: {subgoal}"
        )
        return subgoal

    def validate_result(self, task: Task) -> tuple[bool, str]:
        validation_errors: str = ""

        new_task = TaskFileUtils.load_task(task.id)
        if not new_task.plan:
            validation_errors += "Plan steps must be created for a task."
        
        status = False if validation_errors else True
        return (status, validation_errors)
