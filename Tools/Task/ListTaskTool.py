
import json
from pathlib import Path
from typing import List

from Tasks.Task import Task
from Tools.Tool import Tool

class ListTasksTool(Tool):

    name = "list_tasks"

    description = """
    Returns all stored tasks.
    """

    tags = [
        "tasks",
        "persistence",
        "query"
    ]

    capabilities = [
        "read_tasks"
    ]


    def __init__(
        self,
        base_path: str = "tasks"
    ):
        self.base_path = Path(base_path)


    def run(self) -> List[Task]:

        tasks = []

        for file in self.base_path.glob(
            "*.json"
        ):

            data = json.loads(
                file.read_text()
            )

            tasks.append(
                Task(**data)
            )

        return tasks