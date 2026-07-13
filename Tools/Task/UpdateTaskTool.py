import json
from pathlib import Path

from Tasks.Task import Task
from Tools.Tool import Tool

class UpdateTaskTool(Tool):

    name = "update_task"

    description = """
    Updates an existing task with a complete Task object.
    Used by Planner, Developer, and Tester agents.
    """

    tags = [
        "tasks",
        "persistence",
        "filesystem"
    ]

    capabilities = [
        "update_tasks"
    ]


    def __init__(
        self,
        base_path: str = "tasks"
    ):
        self.base_path = Path(base_path)


    def run(self, task: Task) -> dict:

        file_path = (
            self.base_path /
            f"{task.id}.json"
        )


        if not file_path.exists():
            raise ValueError(
                f"Task does not exist: {task.id}"
            )


        file_path.write_text(
            json.dumps(
                task.model_dump(),
                indent=2
            ),
            encoding="utf-8"
        )


        return {
            "status": "updated",
            "task_id": task.id
        }