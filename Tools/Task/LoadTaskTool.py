import json
from pathlib import Path
from typing import Optional

from Tasks.Task import Task
from Tools.Tool import Tool

class LoadTaskTool(Tool):

    name = "load_task"

    description = """
    Loads a task from persistent storage by task id.
    """

    tags = [
        "tasks",
        "persistence",
        "filesystem"
    ]

    capabilities = [
        "read_tasks"
    ]


    def __init__(
        self,
        base_path: str = "tasks"
    ):
        self.base_path = Path(base_path)


    def run(self, task_id: str) -> Optional[Task]:

        file_path = (
            self.base_path /
            f"{task_id}.json"
        )

        if not file_path.exists():
            return None


        data = json.loads(
            file_path.read_text(
                encoding="utf-8"
            )
        )

        return Task(**data)