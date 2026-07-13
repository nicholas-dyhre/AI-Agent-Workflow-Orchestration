import json
from pathlib import Path

from Tasks.Task import Task
from Tools.Tool import Tool

class PatchTaskTool(Tool):

    name = "patch_task"

    description = """
    Applies partial updates to an existing task.
    Useful for status updates and metadata changes.
    """

    tags = [
        "tasks",
        "persistence"
    ]

    capabilities = [
        "modify_tasks"
    ]


    def __init__(
        self,
        base_path: str = "tasks"
    ):
        self.base_path = Path(base_path)


    def run(
        self,
        task_id: str,
        updates: dict
    ) -> Task:


        file_path = (
            self.base_path /
            f"{task_id}.json"
        )


        if not file_path.exists():
            raise ValueError(
                f"Task not found: {task_id}"
            )


        current = json.loads(
            file_path.read_text()
        )


        current.update(updates)


        updated = Task(**current)


        file_path.write_text(
            json.dumps(
                updated.model_dump(),
                indent=2
            )
        )


        return updated
