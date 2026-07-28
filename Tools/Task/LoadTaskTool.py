import json
from pathlib import Path
from typing import Any, Optional, Type

from pydantic import BaseModel, Field, PrivateAttr

from Tasks.Task import Task
from Tools.Tool import Tool, ToolOutput
from Tools.models.ToolContextKey import ToolContextKey
from Tools.tool_utils.ToolTag import ToolTag
from Tools.tool_utils.ToolCapability import ToolCapability

class LoadTaskInput(BaseModel):
    task_id: str = Field(
        ...,
        description="The unique identifier (UUID or unique string name) of the task to retrieve."
    )


class LoadTaskOutput(ToolOutput):
    task: Task | None = None
    task_id: str

    def to_string(self) -> str:
        result = super().to_string()
        
        if self.task_id:
            result += (
                f"- Task ID: {self.task_id}\n"
            )
        if self.task:
            result += (
                f"- Task loaded successfully \n"
            )
        return result



class LoadTaskTool(Tool[LoadTaskInput, LoadTaskOutput]):
    name: str = "LoadTaskTool"
    description: str = "Retrieves a single task from persistent disk storage using its unique task ID."
    tags: list[ToolTag] = [ToolTag.TASKS, ToolTag.PERSISTENCE, ToolTag.FILESYSTEM]
    capabilities: list[ToolCapability] = [ToolCapability.READ_TASKS]
    path: str = "Tools/LoadTaskTool.py"
    input_model: Type[LoadTaskInput] = LoadTaskInput
    output_model: Type[LoadTaskOutput] = LoadTaskOutput

    _task_base_path: Optional[str] = PrivateAttr()
    
    def initialize(self, context: dict[ToolContextKey, Any]) -> None:
        task_base_path = context[ToolContextKey.task_base_path]
        if task_base_path is None:
            raise Exception("No task base path provided in context")
        if not isinstance(task_base_path, str):
            raise TypeError("task_base_path must be a str")

        self._task_base_path = task_base_path


    def run(self, input: LoadTaskInput) -> LoadTaskOutput:
        if not self._task_base_path:
            raise Exception("Task base path must be provided in context")
        path = Path(self._task_base_path)
        file_path = path / f"{input.task_id}.json"

        if not file_path.exists():
            return LoadTaskOutput(
                success = False,
                task_id=input.task_id,
                message=f"Task '{input.task_id}' was not found."
            )

        try:
            data = json.loads(
                file_path.read_text(encoding="utf-8")
            )

            task = Task(**data)

            return LoadTaskOutput(
                success=True,
                task=task,
                task_id=input.task_id,
                message="Task successfully loaded."
            )

        except (json.JSONDecodeError, TypeError, KeyError) as e:
            raise RuntimeError(
                f"Failed to parse task file for ID '{input.task_id}': {e}"
            )