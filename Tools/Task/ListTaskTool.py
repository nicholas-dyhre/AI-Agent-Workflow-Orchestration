from typing import Type
from pydantic import BaseModel
from Tasks.Task import Task
from Tools.Tool import Tool, ToolOutput
from Tools.tool_utils.ToolTag import ToolTag
from Tools.tool_utils.ToolCapability import ToolCapability
from Tools.Task.TaskFileUtils import TaskFileUtils


class ListTasksInput(BaseModel):
    pass


class ListTasksOutput(ToolOutput):
    tasks: list[Task]
    task_count: int
    skipped_files: list[str]

    def to_string(self) -> str:
        result = super().to_string()
        result += (
            f"- Task Count: {self.task_count}\n"
        )

        if self.tasks:
            result += "\nTasks:\n"
            for task in self.tasks:
                result += f"  - {task.id}: {task.title} ({task.status})\n"

        if self.skipped_files:
            result += "\nSkipped Files:\n" + "\n".join(f"  - {file}" for file in self.skipped_files)

        return result


class ListTasksTool(Tool[ListTasksInput, ListTasksOutput]):
    name: str = "ListTasksTool"
    description: str = "Scans the specified tasks storage directory and retrieves a structured list of all currently saved tasks."
    tags: list[ToolTag] = [ToolTag.TASKS, ToolTag.PERSISTENCE, ToolTag.QUERY]
    capabilities: list[ToolCapability] = [ToolCapability.READ_TASKS]
    path: str = "Tools/ListTasksTool.py"
    input_model: Type[ListTasksInput] = ListTasksInput
    output_model: Type[ListTasksOutput] = ListTasksOutput

    def run(self, input_data: ListTasksInput) -> ListTasksOutput:
        try:
            tasks, skipped_files = TaskFileUtils.load_all_tasks()

            return ListTasksOutput(
                success=True,
                tasks=tasks,
                task_count=len(tasks),
                skipped_files=skipped_files,
                message="Tasks successfully loaded."
            )
        except Exception as e:
            return ListTasksOutput(
                success=False,
                tasks=[],
                task_count=0,
                skipped_files=[],
                message=f"Failed to load tasks: {e}"
            )
