import re
import subprocess
from Agent.AgentNames import AgentName
from Agent.BaseAgent import BaseAgent
from Agent.AgentResponse import AgentResponse
from LLM.LLM import LLM
from Skills.skill_utils.SkillSelector import SkillSelector
from Tools.tool_utils.ToolSelector import ToolSelector
from Tasks.Task import Task, PlanStepState, PlanStep, CodeChange
from Tools.tool_utils.ToolCapability import ToolCapability
from Tools.tool_utils.ToolTag import ToolTag



class DeveloperAgent(BaseAgent):
    def __init__(self, llm: LLM, tool_selector: ToolSelector, skill_selector: SkillSelector):
        super().__init__(llm, tool_selector, skill_selector)
        self.name = AgentName.DEVELOPER.value
        self.agentName = AgentName.DEVELOPER
        self.allowed_tags.extend([ToolTag.FILESYSTEM, ToolTag.DEVELOPMENT, ToolTag.GIT, ToolTag.TESTING])
        self.allowed_capabilities.extend([ToolCapability.WRITE_FILES, ToolCapability.RUN_TESTS, ToolCapability.CREATE_BRANCH, ToolCapability.CREATE_PULL_REQUEST])

    def run(self, task: Task) -> Task:
        self.prepare(task)

        for plan_step in task.plan:
            if plan_step.status not in [PlanStepState.PENDING, PlanStepState.IN_PROGRESS]:
                continue

            planExecuted: AgentResponse = self.execute_plan_step(plan_step)
            commit_message: str = (
                f"task id: {task.id}, plan_step: {plan_step.id}, task title: {task.title}"
            )
            commit_hash: str = self.commit_plan_step(commit_message)

            diff = self.get_diff_for_commit(commit_hash)
            files = self.get_files_changed(commit_hash)

            code_change = CodeChange(
                id=plan_step.id,
                branch_name=task.branch_name,
                commit_hash=commit_hash,
                diff=diff,
                files_changed=files,
                commit_message=commit_message,
                author=self.name,
            )

            task.code_changes.append(code_change)

            plan_step.status = PlanStepState.COMPLETED
            plan_step.assigned_agent = self.agentName

        return task

    def get_files_changed(self, commit_hash: str) -> list[str]:
        result = subprocess.run(
            ["git", "show", "--name-only", "--pretty=format:", commit_hash],
            capture_output=True,
            text=True,
            check=True,
        )

        return [f for f in result.stdout.splitlines() if f]

    def execute_plan_step(self, plan_step: PlanStep) -> AgentResponse:
        prompt = self.build_prompt(plan_step)
        response = self.ReActObs_stream(prompt)
        return response

    def get_diff_for_commit(self, commit_hash: str) -> str:
        result = subprocess.run(
            ["git", "show", commit_hash], capture_output=True, text=True, check=True
        )
        return result.stdout

    def commit_plan_step(self, message: str) -> str:
        result = subprocess.run(["git", "commit", "-m", message], check=True)

        result = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
        )

        commit_hash = result.stdout.strip()
        return commit_hash

    def _extract_commit_hash(self, git_output: str) -> str:
        match = re.search(r"\b[0-9a-f]{7,40}\b", git_output)
        return match.group(0) if match else "unknown"
