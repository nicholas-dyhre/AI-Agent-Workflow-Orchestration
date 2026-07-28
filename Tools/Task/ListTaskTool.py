import json
from pathlib import Path
from typing import Any, Optional, Type

from pydantic import BaseModel, Field, PrivateAttr

from Tasks.Task import Task
from Tools.Tool import Tool, ToolOutput
from Tools.models.ToolContextKey import ToolContextKey
from Tools.tool_utils.ToolTag import ToolTag
from Tools.tool_utils.ToolCapability import ToolCapability

class ListTasksInput(BaseModel):
    void: None = Field(
        default=None,
        description="Input '{}' is valid."
    )


class ListTasksOutput(ToolOutput):
    tasks: list[Task]
    task_count: int
    skipped_files: list[str]
    message: str

    def to_string(self) -> str:
        result = (
            f"- Task Count: {self.task_count}\n"
            f"- Message: {self.message}\n"
        )

        if self.tasks:
            result += "\nTasks:\n"

            for task in self.tasks:
                result += (
                    f"  - {task.id}: {task.title} "
                    f"({task.status})\n"
                )

        if self.skipped_files:
            result += (
                "\nSkipped Files:\n"
                + "\n".join(
                    f"  - {file}"
                    for file in self.skipped_files
                )
            )

        return result


class ListTasksTool(Tool[ListTasksInput, ListTasksOutput]):
    name: str = "ListTasksTool"
    description: str = "Scans the specified tasks storage directory and retrieves a structured list of all currently saved tasks."
    tags: list[ToolTag] = [ToolTag.TASKS, ToolTag.PERSISTENCE, ToolTag.QUERY]
    capabilities: list[ToolCapability] = [ToolCapability.READ_TASKS]
    path: str = "Tools/ListTasksTool.py"
    input_model: Type[ListTasksInput] = ListTasksInput
    output_model: Type[ListTasksOutput] = ListTasksOutput

    _task_base_path: Optional[str] = PrivateAttr()
    
    def initialize(self, context: dict[ToolContextKey, Any]) -> None:
        task_base_path = context[ToolContextKey.task_base_path]
        if task_base_path is None:
            raise Exception("No task base path provided in context")
        if not isinstance(task_base_path, str):
            raise TypeError("task_base_path must be a str")

        self._task_base_path = task_base_path

    def run(self, input: ListTasksInput = ListTasksInput()) -> ListTasksOutput:
        if not self._task_base_path:
            raise Exception("Task base path must be provided in context")
        path = Path(self._task_base_path)

        tasks: list[Task] = []
        skipped_files: list[str] = []

        if not path.exists():
            return ListTasksOutput(
                success=False,
                tasks=[],
                task_count=0,
                skipped_files=[],
                message="Task storage directory does not exist."
            )

        for file in path.glob("*.json"):
            try:
                data = json.loads(
                    file.read_text(encoding="utf-8")
                )

                tasks.append(
                    Task(**data)
                )

            except (json.JSONDecodeError, TypeError, KeyError) as e:
                skipped_files.append(file.name)
                print(
                    f"[ListTasksTool] Warning: Failed to parse task file {file.name}: {e}"
                )

        return ListTasksOutput(
            success=True,
            tasks=tasks,
            task_count=len(tasks),
            skipped_files=skipped_files,
            message="Tasks successfully loaded."
        )