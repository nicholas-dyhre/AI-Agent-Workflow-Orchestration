from Agent.BaseAgent import BaseAgent
from Agent.AgentNames import AgentName
from Tasks.Task import PlanStepReviewState, PlanStepState, Task
from LLM.LLM import LLM
from Skills.skill_utils.SkillSelector import SkillSelector
from Tools.Git.GitUtils import GitUtils
from Tools.code.GetDiffTool import GetDiffTool
from Tools.code.RunProjectTool import RunProjectTool
from Tools.tool_utils.ToolCapability import ToolCapability
from Tools.tool_utils.ToolSelector import ToolSelector
from Tools.tool_utils.ToolTag import ToolTag

class ReviewerAgent(BaseAgent):
    def __init__(self, llm: LLM, tool_selector: ToolSelector, skill_selector: SkillSelector):
        super().__init__(llm, tool_selector, skill_selector)
        self.name = AgentName.REVIEWER.value
        self.agentName = AgentName.REVIEWER
        # Permissions to allow reading and mutating task structures
        self.toolRepository.allowed_tags.extend([ToolTag.PERSISTENCE, ToolTag.QUERY, ToolTag.LOGGING, ToolTag.GIT, ToolTag.TESTING, ToolTag.PERSISTENCE, ToolTag.PERSISTENCE])
        self.toolRepository.allowed_capabilities.extend([
            ToolCapability.MODIFY_TASKS, 
            ToolCapability.SAVE_TASKS, 
            ToolCapability.WRITE_TASK_LOGS, 
            ToolCapability.RUN_TESTS, 
            ToolCapability.GET_CODE_CHANGES,
        ])
        self.toolRepository.denied_capabilities.extend([
            ToolCapability.CREATE_TASK, 
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
            ToolCapability.READ_TASKS,
            ToolCapability.MODIFY_PLAN_STEP
            ])
        # self.goal_checker_tools.extend([
        #     GetDiffTool,
        #     RunProjectTool
        # ])

    def run(self, task: Task):
        for plan_step in task.plan:
            if plan_step.status not in [PlanStepState.COMPLETED]:
                continue
            if plan_step.review is not PlanStepReviewState.APPROVED:
                self.ReActObs_stream(task, plan_step)

    def get_current_goal(self, task: Task) -> str:
        subgoal = f"Review the code solution for: {task.description} \n"
        if task.branch_name:
            _, success = GitUtils.checkout_branch(task.branch_name)
            if success is True:
                diff = GitUtils.get_rich_contextual_diff()
                if diff:
                    subgoal += f"The diff is:\n {diff}"
                else:
                    subgoal += f"No diff found."
            else:
                raise Exception(f"Failed to checkout branch {task.branch_name}")
        else:
            raise Exception("Branch name is required for code review.")

        print(
            f"Agent: {self.name}"
            f"Current subgoal: {subgoal}"
        )
        return subgoal
    
    # def run(self, task: Task) -> Task:
    #     # Safety check: Ensure there is actually a plan step marked for review
    #     # (e.g., set to COMPLETED by developer but waiting on Reviewer approval)
    #     steps_to_review = [s for s in task.plan if s.status.name in ["COMPLETED", "IN_PROGRESS"]]
    #     if not steps_to_review:
    #         print(f"[{self.name}] Warning: No active plan steps found to review.")

    #     print(f"[{self.name}] Reviewing code changes for task: {task.title}")

    #     # Execute the streaming ReAct loop. The agent will call PatchTaskTool internally.
    #     self.execute_review_cycle(task)

    #     # Reload the task from disk to inspect the state mutation made by the tool
    #     patched_task = self._reload_task(task.id)
    #     return patched_task

    # def execute_review_cycle(self, task: Task) -> AgentResponse:
    #     prompt = self.build_prompt(task)

    #     # Provide contextual data regarding git details inside the prompt
    #     code_context = "\n\n### Code Changes To Review:\n"
    #     for change in task.code_changes:
    #         code_context += (
    #             f"Author: {change.author}\n"
    #             f"Branch: {change.branch_name}\n"
    #             f"Commit Message: {change.commit_message}\n"
    #             f"Diff Payload:\n{change.diff}\n"
    #             f"----------------------------------------\n"
    #         )

    #     review_instruction = (
    #         f"\n\nCRITICAL INSTRUCTION: You are the code reviewer. Inspect the Code Changes provided above "
    #         f"against the Task requirements and the requested Plan steps. "
    #         f"You MUST use the 'patch_task' tool to update the task before finishing.\n\n"
    #         f"DECISION MATRIX:\n"
    #         f"1. If ALL code looks correct and matches requirements, update the Task 'status' to 'READY_FOR_MERGE'.\n"
    #         f"2. If there are bugs, syntax issues, or missing criteria, update the Task 'status' back to 'IN_PROGRESS' (or your dev loop state) so the Coder can fix it.\n\n"
    #         f"When invoking 'patch_task', provide these parameters:\n"
    #         f"- 'task_id': '{task.id}'\n"
    #         f"- 'updates': A partial JSON matching these exact schema structural expectations:\n\n"
    #         f"{self.get_patch_review_schema()}\n\n"
    #         f"Be sure to populate the 'review' block inside the target PlanStep objects "
    #         f"setting 'status' to 1 (APPROVED) or 2 (REJECTED), increment 'review_rounds' by 1, and add feedback to the comments. "
    #         f"Once your tool call confirms success, execute your 'final' action to exit."
    #     )

    #     response = self.ReActObs_stream(prompt + code_context + review_instruction)
    #     return response

    # def get_patch_review_schema(self) -> str:
    #     full_schema = Task.model_json_schema()
    #     patch_schema = {
    #         "type": "object",
    #         "properties": {
    #             "status": full_schema["properties"]["status"],  # Transitions State
    #             "review_rounds": full_schema["properties"]["review_rounds"],
    #             "plan": full_schema["properties"]["plan"],  # Updates review remarks per step
    #         },
    #         "$defs": full_schema.get("$defs", {}),
    #     }
    #     return json.dumps(patch_schema, indent=4)

    # def _reload_task(self, task_id: str) -> Task:
    #     import os

    #     file_path = f"tasks/{task_id}.json"
    #     if os.path.exists(file_path):
    #         with open(file_path, "r") as f:
    #             return Task.model_validate_json(f.read())
    #     raise RuntimeError(f"Could not reload task file for id: {task_id}")
