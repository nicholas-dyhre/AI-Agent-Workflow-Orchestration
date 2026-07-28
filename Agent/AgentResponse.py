from typing import Any, Literal, Optional
from pydantic import BaseModel
from enum import Enum


class AgentAction(Enum):
    Tool = "tool"
    Final = "final"

    @staticmethod
    def from_string(value: str) -> "AgentAction":
        return AgentAction(value)

class AgentResponse(BaseModel):
    action: Literal["tool", "final"]
    tool_name: Optional[str] = None
    input: Optional[dict[str, Any]] = None
    final_answer: Optional[str] = None
    reasoning: str
