import json
from pathlib import Path
from typing import Any, Optional, Type

from pydantic import BaseModel, Field, PrivateAttr

from Tasks.Task import Task
from Tools.Tool import Tool, ToolOutput
from Tools.models.ToolContextKey import ToolContextKey
from Tools.tool_utils.ToolTag import ToolTag
from Tools.tool_utils.ToolCapability import ToolCapability


class SaveTaskInput(BaseModel):
    task: Task = Field(
        ...,
        description="The complete structured Task object model data payload that needs to be persisted to storage."
    )
    base_path: str = Field(
        default="tasks",
        description="The directory path relative to the project root where the JSON task file should be written."
    )


class SaveTaskOutput(ToolOutput):
    task_id: str
    saved_path: str

    def to_string(self) -> str:
        result = super().to_string()
        
        if self.task_id:
            result += (
                f"- Task Id: {self.task_id}\n"
            )
        if self.saved_path:
            result += (
                f"- Saved path: {self.saved_path}\n"
            )
    
        return result


class SaveTaskTool(Tool[SaveTaskInput, SaveTaskOutput]):
    name: str = "SaveTaskTool"
    description: str = "Creates a new task file or completely overwrites an existing task on disk for long-term state persistence."
    tags: list[ToolTag] = [ToolTag.TASKS, ToolTag.PERSISTENCE, ToolTag.FILESYSTEM]
    capabilities: list[ToolCapability] = [ToolCapability.SAVE_TASKS]
    path: str = "Tools/SaveTaskTool.py"
    input_model: Type[SaveTaskInput] = SaveTaskInput
    output_model: Type[SaveTaskOutput] = SaveTaskOutput

    _task_base_path: Optional[str] = PrivateAttr()
    
    def initialize(self, context: dict[ToolContextKey, Any]) -> None:
        task_base_path = context[ToolContextKey.task_base_path]
        if task_base_path is None:
            raise Exception("No task base path provided in context")
        if not isinstance(task_base_path, str):
            raise TypeError("task_base_path must be a str")

        self._task_base_path = task_base_path

    def run(self, input: SaveTaskInput) -> SaveTaskOutput:
        if not self._task_base_path:
            raise Exception("Task base path must be provided in context")
        path = Path(self._task_base_path)

        path.mkdir(
            parents=True,
            exist_ok=True
        )

        task_data = input.task
        file_path = path / f"{task_data.id}.json"

        if not task_data.id:
            return SaveTaskOutput(
                success = False,
                task_id=task_data.id,
                saved_path=str(file_path),
                message="Task cannot be written to disk because it is missing a mandatory 'title' string property."
            )

        if not task_data.title:
            return SaveTaskOutput(
                success = False,
                task_id=task_data.id,
                saved_path=str(file_path),
                message="Task cannot be written to disk because it is missing a valid 'id' property."
            )

        file_path.write_text(
            json.dumps(
                task_data.model_dump(),
                indent=2,
                ensure_ascii=False
            ),
            encoding="utf-8"
        )

        return SaveTaskOutput(
            success = True,
            task_id=task_data.id,
            saved_path=str(file_path),
            message="Task successfully saved to persistent storage."
        )