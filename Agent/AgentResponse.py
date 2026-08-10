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
    final_answer: Optional[str | None] = None
    reasoning: str
    goal: str

    def to_string(self) -> str:
        lines = [f"Action: {self.action}"]
        
        if self.tool_name:
            lines.append(f"Tool Name: {self.tool_name}")
            lines.append(f"Input: {self.input}")
        if self.final_answer:
            lines.append(f"Final Answer: {self.final_answer}")
        lines.append(f"Reasoning: {self.reasoning}")
        lines.append(f"Goal: {self.goal}")
        
        return "\n".join(lines)
