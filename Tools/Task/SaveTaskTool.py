import json
from pathlib import Path

from Tasks.Task import Task
from Tools.Tool import Tool

class SaveTaskTool(Tool):

    name = "save_task"

    description = """
    Creates a new task file or overwrites an existing task.
    Used by ProjectPlanner to persist generated tasks.
    """

    tags = [
        "tasks",
        "persistence",
        "filesystem"
    ]

    capabilities = [
        "save_tasks"
    ]

    def __init__(self, base_path: str = "tasks"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(
            parents=True,
            exist_ok=True
        )


    def _get_file_path(self, task_id: str) -> Path:
        return self.base_path / f"{task_id}.json"


    def run(self, task: Task) -> dict:

        self.validate(task)

        file_path = self._get_file_path(task.id)

        with open(
            file_path,
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(
                task.model_dump(),
                f,
                indent=2
            )

        return {
            "status": "saved",
            "task_id": task.id,
            "path": str(file_path)
        }


    def validate(self, task: Task):

        if not task.id:
            raise ValueError(
                "Task requires an id"
            )

        if not task.title:
            raise ValueError(
                "Task requires a title"
            )



