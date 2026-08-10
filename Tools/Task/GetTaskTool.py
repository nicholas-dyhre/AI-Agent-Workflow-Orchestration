from pathlib import Path
from typing import Any, Optional, Type

from pydantic import BaseModel, Field, PrivateAttr

from Tasks.Task import Task
from Tools.Tool import Tool, ToolOutput
from Tools.models.ToolContextKey import ToolContextKey
from Tools.tool_utils.ToolTag import ToolTag
from Tools.tool_utils.ToolCapability import ToolCapability
from Tools.Task.TaskFileUtils import TaskFileUtils


class GetTaskInput(BaseModel):
    task_id: str = Field(
        ...,
        description="Writing the exact string '{{TASK_ID}}' will ensure infrastructure inserts correct taskid."
    )


class GetTaskOutput(ToolOutput):
    task: Optional[Task] = None
    message: str

    def to_string(self) -> str:
        result = super().to_string()
        if self.task:
            result += (
                f"\nTask Found:\n"
                f"  - ID: {self.task.id}\n"
                f"  - Title: {self.task.title}\n"
                f"  - Status: {self.task.status}\n"
            )
        return result


class GetTaskTool(Tool[GetTaskInput, GetTaskOutput]):
    name: str = "GetTaskTool"
    description: str = "Retrieves a single structured Task from storage using its unique task ID."
    tags: list[ToolTag] = [ToolTag.TASKS, ToolTag.PERSISTENCE, ToolTag.QUERY]
    capabilities: list[ToolCapability] = [ToolCapability.READ_TASKS]
    path: str = "Tools/GetTaskTool.py"
    input_model: Type[GetTaskInput] = GetTaskInput
    output_model: Type[GetTaskOutput] = GetTaskOutput

    def run(self, input_data: GetTaskInput) -> GetTaskOutput:
        try:
            task = TaskFileUtils.load_task(input_data.task_id)

            return GetTaskOutput(
                success=True,
                task=task,
                message=f"Task '{input_data.task_id}' successfully loaded."
            )
        except Exception as e:
            return GetTaskOutput(
                success=False,
                task=None,
                message=f"Failed to load task '{input_data.task_id}': {e}"
            )
