import json
from pathlib import Path
from typing import Any, Optional, Type

from pydantic import BaseModel, Field, PrivateAttr

from Tools.Tool import Tool, ToolOutput
from Tools.models.ToolContextKey import ToolContextKey
from Tools.tool_utils.ToolTag import ToolTag
from Tools.tool_utils.ToolCapability import ToolCapability

class AppendTaskLogToolInput(BaseModel):
    task_id: str = Field(
        ...,
        description="Id of the task to append to"
    )
    log_entry: dict = Field(
        ...,
        description="The log to append to the tasks log list"
    )


class AppendTaskLogToolOutput(ToolOutput):
    task_id: str

    def to_string(self) -> str:
        return (
            f"- Task ID: {self.task_id}"
        )


class AppendTaskLogTool(Tool[AppendTaskLogToolInput, AppendTaskLogToolOutput]):
    name: str = "AppendTaskLogTool"
    description: str = "Adds an agent execution log entry to a task."
    tags: list[ToolTag] = [ToolTag.TASKS, ToolTag.LOGGING, ToolTag.PERSISTENCE]
    capabilities: list[ToolCapability] = [ToolCapability.WRITE_TASK_LOGS]
    path: str = "Tools/AppendTaskLogTool.py"
    input_model: Type[AppendTaskLogToolInput] = AppendTaskLogToolInput
    output_model: Type[AppendTaskLogToolOutput] = AppendTaskLogToolOutput

    _task_base_path: Optional[str] = PrivateAttr()
    
    def initialize(self, context: dict[ToolContextKey, Any]) -> None:
        task_base_path = context[ToolContextKey.task_base_path]
        if task_base_path is None:
            raise Exception("No task base path provided in context")
        if not isinstance(task_base_path, str):
            raise TypeError("task_base_path must be a str")

        self._task_base_path = task_base_path

    def run(self, input: AppendTaskLogToolInput) -> AppendTaskLogToolOutput:
        if not self._task_base_path:
            raise Exception("Task base path must be provided in context")
        path = Path(self._task_base_path)

        file_path = path / f"{input.task_id}.json"

        if not file_path.exists():
            return AppendTaskLogToolOutput(
                success=False,
                message = f"Task not found: {input.task_id}",
                task_id = input.task_id,
            )
            
        data = json.loads(file_path.read_text(encoding="utf-8"))

        if "logs" not in data:
            data["logs"] = []

        data["logs"].append(input.log_entry)

        file_path.write_text(
            json.dumps(data, indent=2),
            encoding="utf-8"
        )

        return AppendTaskLogToolOutput(
            success=True,
            message = "Log added successfully.",
            task_id = input.task_id,
        )