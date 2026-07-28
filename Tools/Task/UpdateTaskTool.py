import json
from pathlib import Path
from typing import Any, Optional, Type

from pydantic import BaseModel, Field, PrivateAttr

from Tasks.Task import Task
from Tools.Tool import Tool, ToolOutput
from Tools.models.ToolContextKey import ToolContextKey
from Tools.tool_utils.ToolTag import ToolTag
from Tools.tool_utils.ToolCapability import ToolCapability


class UpdateTaskInput(BaseModel):
    task: Task = Field(
        ...,
        description="The complete updated Task object model data payload that will overwrite the existing file."
    )
    base_path: str = Field(
        default="tasks",
        description="The directory path relative to the project root where the JSON task files are stored."
    )


class UpdateTaskOutput(ToolOutput):
    task_id: str
    updated_path: str

    def to_string(self) -> str:
        result = super().to_string()
        
        if self.task_id:
            result += (
                f"- Task Id: {self.task_id}\n"
            )
        if self.updated_path:
            result += (
                f"- Updated path: {self.updated_path}\n"
            )
    
        return result


class UpdateTaskTool(Tool[UpdateTaskInput, UpdateTaskOutput]):
    name: str = "UpdateTaskTool"
    description: str = "Updates an existing task in persistent storage by overwriting it with a complete, updated Task object model payload."
    tags: list[ToolTag] = [ToolTag.TASKS, ToolTag.PERSISTENCE, ToolTag.FILESYSTEM]
    capabilities: list[ToolCapability] = [ToolCapability.UPDATE_TASKS]
    path: str = "Tools/UpdateTaskTool.py"
    input_model: Type[UpdateTaskInput] = UpdateTaskInput
    output_model: Type[UpdateTaskOutput] = UpdateTaskOutput
    _task_base_path: Optional[str] = PrivateAttr()

    def initialize(self, context: dict[ToolContextKey, Any]) -> None:
        task_base_path = context[ToolContextKey.task_base_path]
        if task_base_path is None:
            raise Exception("No task base path provided in context")
        if not isinstance(task_base_path, str):
            raise TypeError("task_base_path must be a str")

        self._task_base_path = task_base_path

    def run(self, input: UpdateTaskInput) -> UpdateTaskOutput:
        if not self._task_base_path:
            raise Exception("Task base path must be provided in context")
        path = Path(self._task_base_path)
        task_data = input.task
        file_path = path / f"{task_data.id}.json"

        if not task_data.id:
            return UpdateTaskOutput(
                success = True,
                task_id=task_data.id,
                updated_path=str(file_path),
                message="Task update rejected because the provided Task object is missing a valid 'id'."
            )        

        if not file_path.exists():
            return UpdateTaskOutput(
                success = True,
                task_id=task_data.id,
                updated_path=str(file_path),
                message=f"Task matching ID '{task_data.id}' does not exist in storage. "
                                "Use 'save_task' to create new records."
            )

        file_path.write_text(
            json.dumps(
                task_data.model_dump(),
                indent=2,
                ensure_ascii=False
            ),
            encoding="utf-8"
        )

        return UpdateTaskOutput(
            success = True,
            task_id=task_data.id,
            updated_path=str(file_path),
            message="Task successfully updated in persistent storage."
        )