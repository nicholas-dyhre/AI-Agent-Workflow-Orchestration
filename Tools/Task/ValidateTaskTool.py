from typing import Type
from pydantic import BaseModel, Field
from Tasks.Task import Task
from Tools.Tool import Tool, ToolOutput
from Tools.tool_utils.ToolTag import ToolTag
from Tools.tool_utils.ToolCapability import ToolCapability


class ValidateTaskInput(BaseModel):
    task: Task = Field(
        ...,
        description="The complete structured Task object model data payload that needs to be evaluated for schema and business rule validity."
    )


class ValidateTaskOutput(ToolOutput):
    task_id: str

    def to_string(self) -> str:
        result = super().to_string()
        
        if self.task_id:
            result += (
                f"- Task Id: {self.task_id}\n"
            )

        return result


class ValidateTaskTool(Tool[ValidateTaskInput, ValidateTaskOutput]):
    name: str = "ValidateTaskTool"
    description: str = "Validates that a provided Task object meets all strict structural configurations and lifecycle state requirements."
    tags: list[ToolTag] = [ToolTag.TASKS, ToolTag.VALIDATION]
    capabilities: list[ToolCapability] = [ToolCapability.VALIDATE_TASKS]
    path: str = "Tools/ValidateTaskTool.py"
    input_model: Type[ValidateTaskInput] = ValidateTaskInput
    output_model: Type[ValidateTaskOutput] = ValidateTaskOutput

    def run(self, input: ValidateTaskInput) -> ValidateTaskOutput:
        task_data = input.task

        if not task_data.id:
            raise ValueError(
                "Task validation failed: The property 'id' is missing or empty."
            )

        if not task_data.title:
            raise ValueError(
                "Task validation failed: The property 'title' is missing or empty."
            )

        if not task_data.description:
            raise ValueError(
                "Task validation failed: The property 'description' is missing or empty."
            )

        if task_data.status is None:
            raise ValueError(
                "Task validation failed: The property 'status' is missing."
            )

        return ValidateTaskOutput(
            success=True,
            task_id=task_data.id,
            message="Task passed all structural and lifecycle validation checks."
        )