from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from enum import Enum

from TaskState import State

# Dev and planner status
class PlanStepState(Enum):
    PENDING = 0
    IN_PROGRESS = 1
    COMPLETED = 2

# Review status for each step in the plan
class PlanStepReviewState(Enum):
    NONE = 0     # Not reviewed yet
    APPROVED = 1 # Reviewer agrees the step is complete
    REJECTED = 2 # Dev must redo the step

class PlanStepReviewSeverity(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3

class PlanStepReview(BaseModel):
    reviewer: str
    comments: str
    timestamp: str
    status: PlanStepReviewState
    severity: PlanStepReviewSeverity
    review: str = Field(default="")

class PlanStep(BaseModel):
    id: str
    description: str
    status: PlanStepState
    review: PlanStepReview
    execution_failed_reason: str = Field(default="")
    assigned_agent: str

class CodeChange(BaseModel):
    id: str
    branch_name: Optional[str]
    commit_hash: Optional[str]
    diff: Optional[str]
    files_changed: Optional[List[str]]
    commit_message: Optional[str]
    author: str


class AgentLog(BaseModel):
    agent: str
    input: str
    output: str
    timestamp: str


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