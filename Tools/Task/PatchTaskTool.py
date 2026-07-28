import json
from pathlib import Path
from typing import Any, Dict, Optional, Type

from pydantic import BaseModel, Field, PrivateAttr

from Tasks.Task import Task
from Tools.Tool import Tool, ToolOutput
from Tools.models.ToolContextKey import ToolContextKey
from Tools.tool_utils.ToolTag import ToolTag
from Tools.tool_utils.ToolCapability import ToolCapability


class PatchTaskInput(BaseModel):
    task_id: str = Field(
        ...,
        description="The unique identifier (UUID or unique string name) of the task to update."
    )
    updates: Dict[str, Any] = Field(
        ...,
        description="A key-value dictionary containing the fields to update (e.g., {'status': 'completed', 'priority': 'high'})."
    )
    base_path: str = Field(
        default="tasks",
        description="The directory path relative to the project root where the JSON task files are stored."
    )


class PatchTaskOutput(ToolOutput):
    task: Task
    updated_fields: list[str]

    def to_string(self) -> str:
        result = super().to_string()
        
        if self.task and self.task.id:
            result += (
                f"- Task ID: {self.task.id}\n"
            )
        if self.updated_fields:
            result += (
                f"- Updated Fields: {', '.join(self.updated_fields)}\n"
            )
    
        return result


class PatchTaskTool(Tool[PatchTaskInput, PatchTaskOutput]):
    name: str = "PatchTaskTool"
    description: str = "Applies partial structural modifications (patches) to an existing stored task without overwriting unchanged fields."
    tags: list[ToolTag] = [ToolTag.TASKS, ToolTag.PERSISTENCE]
    capabilities: list[ToolCapability] = [ToolCapability.MODIFY_TASKS]
    path: str = "Tools/PatchTaskTool.py"
    input_model: Type[PatchTaskInput] = PatchTaskInput
    output_model: Type[PatchTaskOutput] = PatchTaskOutput

    _task_base_path: Optional[str] = PrivateAttr()
    
    def initialize(self, context: dict[ToolContextKey, Any]) -> None:
        task_base_path = context[ToolContextKey.task_base_path]
        if task_base_path is None:
            raise Exception("No task base path provided in context")
        if not isinstance(task_base_path, str):
            raise TypeError("task_base_path must be a str")

        self._task_base_path = task_base_path

    def run(self, input: PatchTaskInput) -> PatchTaskOutput:
        if not self._task_base_path:
            raise Exception("Task base path must be provided in context")
        path = Path(self._task_base_path)
        file_path = path / f"{input.task_id}.json"

        if not file_path.exists():
            raise ValueError(
                f"Task matching ID '{input.task_id}' was not found in storage."
            )

        try:
            current_data = json.loads(
                file_path.read_text(encoding="utf-8")
            )

            current_data.update(input.updates)

            updated_task = Task(**current_data)

            file_path.write_text(
                json.dumps(
                    updated_task.model_dump(),
                    indent=2,
                    ensure_ascii=False
                ),
                encoding="utf-8"
            )

            return PatchTaskOutput(
                success = True,
                task=updated_task,
                updated_fields=list(input.updates.keys()),
                message="Task successfully patched and persisted."
            )

        except (json.JSONDecodeError, TypeError, KeyError) as e:
            return PatchTaskOutput(
                success = False,
                task=updated_task,
                updated_fields=list(input.updates.keys()),
                message=f"Failed to apply patch due to a data processing or schema error: {e}"
            )