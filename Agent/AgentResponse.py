from typing import Any, Literal, Optional
from pydantic import BaseModel

class AgentResponse(BaseModel):
    action: Literal["tool", "final"]
    tool_name: Optional[str] = None
    input: Optional[dict[str, Any]] = None
    final_answer: Optional[str] = None