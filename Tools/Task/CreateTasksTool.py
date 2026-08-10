import uuid
from typing import Any, Optional, Type
from pydantic import BaseModel, Field, PrivateAttr, model_validator
from Tasks.TaskState import State
from Tools.Tool import Tool, ToolOutput
from Tools.models.ToolContextKey import ToolContextKey
from Tools.tool_utils.ToolTag import ToolTag
from Tools.tool_utils.ToolCapability import ToolCapability
from Tools.Task.TaskFileUtils import TaskFileUtils

class CreateTasksInput(BaseModel):
    titles: list[str] = Field(
        ...,
        description="A list containing the titles of the tasks you want to create."
    )
    descriptions: list[str] = Field(
        ...,
        description="A list containing descriptions matching each corresponding title in the titles array."
    )

    @model_validator(mode="after")
    def validate_equal_lengths(self) -> "CreateTasksInput":
        if len(self.titles) != len(self.descriptions):
            raise ValueError(
                f"Mismatched array lengths. You provided {len(self.titles)} titles "
                f"but {len(self.descriptions)} descriptions. Every title must have exactly one description."
            )
        return self


class CreateTasksOutput(ToolOutput):
    created_tasks: list[dict[str, Any]]
    created_count: int
    message: str

    def to_string(self) -> str:
        result = super().to_string()
        result += (
            f"- Created Count: {self.created_count}\n"
        )
        if self.created_tasks:
            result += "\nCreated Tasks:\n"
            for task in self.created_tasks:
                result += f"  - ID: {task.get('id')} | Title: {task.get('title')}\n"
        return result


class CreateTasksTool(Tool[CreateTasksInput, CreateTasksOutput]):
    name: str = "CreateTasksTool"
    description: str = "Creates multiple structured tasks simultaneously. Ensures titles and descriptions align one-to-one."
    tags: list[ToolTag] = [ToolTag.TASKS, ToolTag.PERSISTENCE, ToolTag.FILESYSTEM]
    capabilities: list[ToolCapability] = [ToolCapability.WRITE_FILES, ToolCapability.CREATE_TASK, ToolCapability.SAVE_TASKS]
    path: str = "Tools/CreateTasksTool.py"
    input_model: Type[CreateTasksInput] = CreateTasksInput
    output_model: Type[CreateTasksOutput] = CreateTasksOutput

    def run(self, input_data: CreateTasksInput) -> CreateTasksOutput:
        created_records = []
        tasks_data: list[dict[str, Any]] = []
        task_ids: list[str] = []

        try:
            for title, description in zip(input_data.titles, input_data.descriptions):
                task_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, title.strip()))
                
                task_data = {
                    "id": task_id,
                    "title": title.strip(),
                    "description": description.strip(),
                    "status": State.CREATED.value
                }
                tasks_data.append(task_data)
                task_ids.append(task_id)

                created_records.append(TaskFileUtils.create_task(task_data))

        except Exception as e:
            return CreateTasksOutput(
                success=False,
                created_tasks=[],
                created_count=0,
                message=f"Failed to create files. \n Error: {e}."
            )

        if isinstance(created_records, str):
            return CreateTasksOutput(
                success=False,
                created_tasks=[],
                created_count=0,
                message=f"Failed to create tasks. \n Error: {created_records}."
            )
        
        print(f"Tasks saved successfully. {len(created_records)} tasks have been added to the backlog.")
        return CreateTasksOutput(
            success=True,
            created_tasks=created_records,
            created_count=len(created_records),
            message=f"Successfully created and persisted {len(created_records)} new tasks."
        )
