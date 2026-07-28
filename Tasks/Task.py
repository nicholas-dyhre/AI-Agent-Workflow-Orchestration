from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from enum import Enum

from Agent.AgentNames import AgentName
from Tasks.TaskState import State

indentation_step = "  "

# Dev and planner status
class PlanStepState(Enum):
    PENDING = 0
    IN_PROGRESS = 1
    COMPLETED = 2


# Review status for each step in the plan
class PlanStepReviewState(Enum):
    NONE = 0  # Not reviewed yet
    APPROVED = 1  # Reviewer agrees the step is complete
    REJECTED = 2  # Dev must redo the step


class PlanStepReviewSeverity(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


class PlanStepReview(BaseModel):
    reviewer: str = Field(default="")
    comments: str = Field(default="")
    timestamp: str = Field(default="")
    status: PlanStepReviewState = PlanStepReviewState.NONE
    severity: PlanStepReviewSeverity = PlanStepReviewSeverity.LOW
    review: str = Field(default="")

    def to_prompt(self, indentation: str) -> str:            
        return (
            f"{indentation}PlanStepReview\n"
            f"{indentation}- PlanStepReview Reviewer: {self.reviewer}\n"
            f"{indentation}- PlanStepReview Comments: {self.comments}\n"
            f"{indentation}- PlanStepReview Timestamp: {self.timestamp}\n"
            f"{indentation}- PlanStepReview status: {self.status.value}\n"
            f"{indentation}- PlanStepReview severity: {self.severity.value}\n"
            f"{indentation}- PlanStepReview review: {self.review}\n"
        )



class PlanStep(BaseModel):
    id: str
    description: str
    status: PlanStepState = Field(default=PlanStepState.PENDING)
    review: PlanStepReview = Field(default=PlanStepReview())
    execution_failed_reason: str = Field(default="")
    assigned_agent: AgentName = Field(default=AgentName.DEVELOPER)

    def to_prompt(self, indentation: str = "") -> str:
        nextindentation = indentation + indentation_step
        prompt = (
            f"{indentation}PlanStep\n"
            f"{indentation}- PlanStep ID: {self.id}\n"
            f"{indentation}- PlanStep Description: {self.description}\n"
            f"{indentation}- PlanStep Status: {self.status.name}\n"
            f"{indentation}- PlanStep Assigned Agent: {self.assigned_agent.name}\n"
        )
        if self.review and self.review.status != PlanStepReviewState.NONE:
            prompt += f"{indentation}- PlanStep review: \t {self.review.to_prompt(nextindentation)}\n"
        if self.execution_failed_reason:
            prompt += f"{indentation}- Planstep Execution Failed Reason: {self.execution_failed_reason}\n"
        return prompt


class CodeChange(BaseModel):
    id: str
    branch_name: Optional[str]
    commit_hash: Optional[str]
    diff: Optional[str]
    files_changed: Optional[List[str]]
    commit_message: Optional[str]
    author: str

    def to_prompt(self, indentation: str):
        return (f"{indentation}CodeChange\n"
                f"{indentation}- CodeChange id: {self.id}\n"
                f"{indentation}- CodeChange branch_name: {self.branch_name}\n"
                f"{indentation}- CodeChange commit_hash: {self.commit_hash}\n"
                f"{indentation}- CodeChange diff: {self.diff}\n"
                f"{indentation}- CodeChange files_changed: {self.__files_changed_to_prompt(indentation)}\n"
                f"{indentation}- CodeChange commit_message: {self.commit_message}\n"
                f"{indentation}- CodeChange author: {self.author}\n")

    def __files_changed_to_prompt(self, indentation: str):
        if self.files_changed is None:
            return "No file changes"
        return f"\n".join(f"{indentation}- {file}" for file in self.files_changed)



class AgentLog(BaseModel):
    agent: AgentName
    input: str
    output: str
    timestamp: str

    def to_prompt(self, indentation: str):
        return (f"{indentation}AgentLog Log\n"
                f"{indentation}- AgentLog agent: {self.agent.value}\n"
                f"{indentation}- AgentLog input: {self.input}\n"
                f"{indentation}- AgentLog output: {self.output}\n"
                f"{indentation}- AgentLog timestamp: {self.timestamp}\n")


class Task(BaseModel):
    id: str
    title: str
    description: str
    status: State
    plan: List[PlanStep] = []
    code_changes: List[CodeChange] = []
    logs: List[AgentLog] = []
    metadata: Dict = {}
    review_rounds: int = 0
    branch_name: Optional[str] = None
    pr_url: Optional[str] = None

    def to_prompt(self, agentName: AgentName, indentation = "") -> str:
        prompt = (
            f"{indentation}Task: \n"
            f"{indentation}- Id: {self.id}\n"
            f"{indentation}- Status: {self.status.value}\n"
            f"{indentation}- Description: {self.description}\n"
        )

        if self.branch_name:
            prompt += f"{indentation}- Branch: {self.branch_name}\n"
        if self.pr_url:
            prompt += f"{indentation}- PR: {self.pr_url}\n"
        if self.review_rounds:
            prompt += f"{indentation}. Review Rounds: {self.review_rounds}\n"
        if self.metadata:
            prompt += f"{indentation}- Metadata: \n"
            for metadata in self.metadata.keys():
                prompt += f"{indentation}- {metadata}: {self.metadata[metadata]}\n"

        match agentName:
            case AgentName.DEVELOPER:
                prompt += self.__to_developer_prompt(indentation)
            case AgentName.REVIEWER:
                prompt += self.__to_reviewer_prompt(indentation)
            case AgentName.PLANNER:
                prompt += self.__to_planner_prompt(indentation)

        print(prompt)
        return prompt

    def __to_developer_prompt(self, indentation: str) -> str:
        nextindentation = indentation + indentation_step
        active_steps = [
            step for step in self.plan
            if step.assigned_agent == AgentName.DEVELOPER
            and step.status != PlanStepState.COMPLETED
        ]

        active_steps_text = f"{indentation}- Active PlanSteps\n"

        if not active_steps:
            active_steps_text += f"{indentation}No active development PlanSteps.\n"

        active_steps_text += f"{indentation}Active PlanSteps:\n"
        for step in active_steps:
            active_steps_text += step.to_prompt(nextindentation)

        prompt = active_steps_text
        prompt += f"{indentation}- Logs: {self.__logs_to_prompt(indentation, AgentName.DEVELOPER)}\n"

        if self.code_changes:
            prompt += f"{indentation}- Code Changes\n"
            for code_change in self.code_changes:
                prompt += code_change.to_prompt(nextindentation)
        return prompt

    def __to_reviewer_prompt(self, indentation: str) -> str:
        nextindentation = indentation + indentation_step
        active_steps = [
            step for step in self.plan
            if step.assigned_agent == AgentName.REVIEWER
            and step.status == PlanStepState.IN_PROGRESS
            and step.review.status == PlanStepReviewState.NONE
        ]

        active_steps_text = f"{indentation}- PlanSteps missing review\n"

        if not active_steps:
            active_steps_text += f"{indentation}No PlanSteps missing review.\n"

        active_steps_text += f"{indentation}PlanSteps missing review:\n"
        for step in active_steps:
            active_steps_text += step.to_prompt(nextindentation)

        prompt = active_steps_text
        prompt += f"{indentation}- Logs: {self.__logs_to_prompt(indentation, AgentName.REVIEWER)}\n"

        if self.code_changes:
            prompt += f"{indentation}- Code Changes\n"
            for code_change in self.code_changes:
                prompt += code_change.to_prompt(nextindentation)
        return prompt

    def __to_planner_prompt(self, indentation: str) -> str:
        prompt = f"{indentation}- Logs: {self.__logs_to_prompt(indentation, AgentName.PLANNER)}\n"

        return prompt

    def __logs_to_prompt(self, indentation: str, agentName: AgentName) -> str:
        nextindentation = indentation + indentation_step
        log_prompt = ""
        logs = [
            log for log in self.logs
            if log.agent == agentName
            and log.input or log.output
        ]
        for log in logs:
            log_prompt += log.to_prompt(nextindentation)
        return log_prompt
        

        
