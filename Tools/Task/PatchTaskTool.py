from typing import Any, Dict, Optional, Type

from pydantic import BaseModel, Field, PrivateAttr

from Tasks.Task import Task
from Tools.Tool import Tool, ToolOutput
from Tools.models.ToolContextKey import ToolContextKey
from Tools.tool_utils.ToolTag import ToolTag
from Tools.tool_utils.ToolCapability import ToolCapability
from Tools.Task.TaskFileUtils import TaskFileUtils


class PatchTaskInput(BaseModel):
    task_id: str = Field(
        ...,
        description="Writing the exact string '{{TASK_ID}}' will ensure infrastructure inserts correct taskid."
    )
    updates: Dict[str, Any] = Field(
        ...,
        description="A key-value dictionary containing the fields to update (e.g., {'status': 'completed'})."
    )
    base_path: str = Field(
        default="tasks",
        description="The directory path relative to the project root where the JSON task files are stored."
    )


class PatchTaskOutput(ToolOutput):
    task: Task | None
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
        
        try:
            updated_task = TaskFileUtils.patch_task(input.task_id, input.updates)
        except Exception as e:
            return PatchTaskOutput(
                success = False,
                task=None,
                updated_fields=list(input.updates.keys()),
                message=f"Failed to apply patch due to a data processing or schema error: {e} \n"
            )

        if isinstance(updated_task, str):
            return PatchTaskOutput(
                success = False,
                task=None,
                updated_fields=list(input.updates.keys()),
                message=f"Failed to apply patch. Error: {updated_task} \n"
            )

        return PatchTaskOutput(
            success = True,
            task=updated_task,
            updated_fields=list(input.updates.keys()),
            message="Task successfully patched and persisted. \n"
        )