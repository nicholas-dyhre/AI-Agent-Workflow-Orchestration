from Agent.AgentNames import AgentName
from Agent.BaseAgent import BaseAgent
from LLM.LLM import LLM
from Skills.skill_utils.SkillSelector import SkillSelector
from Tools.Git.GitUtils import GitUtils
from Tools.Task.TaskFileUtils import TaskFileUtils
from Tools.code.CodeUtils import CodeUtils
from Tools.tool_utils.ToolSelector import ToolSelector
from Tasks.Task import PlanStep, Task, PlanStepState
from Tools.tool_utils.ToolCapability import ToolCapability
from Tools.tool_utils.ToolTag import ToolTag
from Tools.code.GetDiffTool import GetDiffTool
from Tools.code.RunProjectTool import RunProjectTool

class DeveloperAgent(BaseAgent):
    def __init__(self, llm: LLM, tool_selector: ToolSelector, skill_selector: SkillSelector):
        super().__init__(llm, tool_selector, skill_selector)
        self.name = AgentName.DEVELOPER.value
        self.agentName = AgentName.DEVELOPER
        self.allowed_tags.extend([ToolTag.FILESYSTEM, ToolTag.DEVELOPMENT, ToolTag.GIT, ToolTag.TESTING, ToolTag.GENERATION])
        self.allowed_capabilities.extend([
            ToolCapability.WRITE_FILES, 
            ToolCapability.RUN_TESTS, 
            ToolCapability.CREATE_PULL_REQUEST, 
            ToolCapability.GIT, 
            ToolCapability.GENERATE_CODE, 
            ToolCapability.GET_CODE_CHANGES,
            ToolCapability.COMMIT_CHANGES,
            ToolCapability.PUSH_CHANGES,
            ToolCapability.GIT_GET_REPO_INFO,
            ToolCapability.CODE,
        ])
        self.denied_capabilities.extend([
            ToolCapability.CREATE_TASK, 
            ToolCapability.CREATE_PLAN_STEP, 
            ToolCapability.READ_TASKS, 
            ToolCapability.READ_PLAN_STEPS
            ])
        self.goal_checker_tools.extend([
            GetDiffTool,
            RunProjectTool
        ])
        self.diff: str = ""

    def run(self, task: Task) -> Task:
        branch_name = task.branch_name if task.branch_name else f"task-{task.id}"
        GitUtils.checkout_branch(branch_name, True)
        status = False
        while status is False:
            for plan_step in task.plan:
                if plan_step.status not in [PlanStepState.PENDING, PlanStepState.IN_PROGRESS]:
                    continue

                planStepStatus = False
                while not planStepStatus:
                    TaskFileUtils.patch_planstep_in_task_file(task.id, plan_step.id, {"status": PlanStepState.IN_PROGRESS})
                    self.ReActObs_stream(task, plan_step)
                    TaskFileUtils.patch_planstep_in_task_file(task.id, plan_step.id, {"status": PlanStepState.COMPLETED})
                    planStepStatus, validation_message = self.validate_planstep(task, plan_step)
                    if not planStepStatus:
                        self.validation_error = validation_message
                    
            status, message = self.validate_result(task)
            if not status:
                self.validation_error = message 
        self.log(
            task.id,
            input=task.description,
            output=f"Developer completed execution.",
        )

        return task

    def get_current_goal(self, planStep: PlanStep) -> str:
        subgoal = f"Build code that solves or accomplishes: {planStep.description}. Use tools to read, write, persist code. Use Tools to add it to a pull request."
        print(
            f"Agent: {self.name}"
            f"Current subgoal: {subgoal}"
        )
        return subgoal

    def validate_planstep(self, task: Task, planStep: PlanStep) -> tuple[bool, str]:
            validation_errors: str = ""

            isEmpty, status = GitUtils.get_repo_status()
            if isEmpty:
                validation_errors = status + "\n"

            diff = GitUtils.get_diff()
            if not diff:
                validation_errors += "No diff found. The task can only be resolved with code changes \n"
            else:
                if self.diff == diff:
                    validation_errors += f"No code changes registered for planstep {planStep.id} \n"
                    TaskFileUtils.patch_planstep_in_task_file(task.id, planStep.id, {"status": PlanStepState.IN_PROGRESS})
                self.diff = diff

            diff_empty = GitUtils.is_diff_empty()
            if diff_empty:
                validation_errors += "Code changes are not registered in git repository. The task can only be resolved with code changes \n"

            runs = CodeUtils.run_project(None)
            for run in runs:
                if not run.execution_output:
                    validation_errors += "No execution output. The task can only be resolved with code changes"
                elif not run.execution_output.is_success():
                    validation_errors +=  f"The project execution failed. StdErr:{run.execution_output.stderr}"
                
            tests = CodeUtils.run_tests(None)
            for test in tests:
                if not test.execution_output:
                    validation_errors +=  "No test output. Ensure that the project runs, has test and tests run successfully."
                elif not test.execution_output.is_success():
                    validation_errors += f"Failed to run tests. StdErr:{test.execution_output.stderr}"

            status = False if validation_errors else True
            return (status, validation_errors)

    def validate_result(self, task: Task) -> tuple[bool, str]:
        validation_errors: str = ""

        
        new_task = TaskFileUtils.load_task(task.id)
        for planstep in new_task.plan:
            if planstep.status is not PlanStepState.COMPLETED:
                validation_errors += "All plansteps must be completed. \n"


        status = False if validation_errors else True
        return (status, validation_errors)

