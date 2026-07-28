import json
import uuid
from pathlib import Path
from typing import Any, Optional, Type
from pydantic import BaseModel, Field, PrivateAttr, model_validator
from Tasks.TaskState import State
from Tools.Tool import Tool, ToolOutput
from Tools.models.ToolContextKey import ToolContextKey
from Tools.tool_utils.ToolTag import ToolTag
from Tools.tool_utils.ToolCapability import ToolCapability

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
        result = (
            f"- Success: {self.success}\n"
            f"- Created Count: {self.created_count}\n"
            f"- Message: {self.message}\n"
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

    _task_base_path: Optional[str] = PrivateAttr()
    
    def initialize(self, context: dict[ToolContextKey, Any]) -> None:
        task_base_path = context[ToolContextKey.task_base_path]
        if task_base_path is None:
            raise Exception("No task base path provided in context")
        if not isinstance(task_base_path, str):
            raise TypeError("task_base_path must be a str")

        self._task_base_path = task_base_path

    def run(self, input: CreateTasksInput) -> CreateTasksOutput:
        if not self._task_base_path:
            print(f"Configuration Error: Task base path must be provided in context.")
            return CreateTasksOutput(
                success=False,
                created_tasks=[],
                created_count=0,
                message="Configuration Error: Task base path must be provided in context."
            )

        write_path = Path(self._task_base_path)
        
        try:
            write_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"File System Error: Unable to verify or create storage directory: {e}")
            return CreateTasksOutput(
                success=False,
                created_tasks=[],
                created_count=0,
                message=f"File System Error: Unable to verify or create storage directory: {e}"
            )

        created_records = []

        for title, description in zip(input.titles, input.descriptions):
            task_id = str(uuid.uuid4())
            
            task_data = {
                "id": task_id,
                "title": title.strip(),
                "description": description.strip(),
                "status": State.CREATED.value
            }

            file_target = write_path / f"{task_id}.json"
            
            try:
                file_target.write_text(
                    json.dumps(task_data, indent=4, ensure_ascii=False), 
                    encoding="utf-8"
                )
                created_records.append(task_data)
            except Exception as e:
                print(f"Task Failed to Save: {e}")
                return CreateTasksOutput(
                    success=False,
                    created_tasks=created_records,
                    created_count=len(created_records),
                    message=f"Partial Save Failure: Process halted while writing task '{title}'. Disk Error: {e}"
                )
        print(f"Tasks saved successfully. {len(created_records)} tasks have been added to the backlog.")
        return CreateTasksOutput(
            success=True,
            created_tasks=created_records,
            created_count=len(created_records),
            message=f"Successfully created and persisted {len(created_records)} new tasks."
        )
