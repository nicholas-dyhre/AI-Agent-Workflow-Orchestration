
import json
from pathlib import Path
from typing import Optional

from Tasks.Task import Task
from Tools.Tool import Tool

class GetNextReadyTaskTool(Tool):

    name = "get_next_ready_task"

    description = """
    Finds the next pending task where all dependencies are completed.
    """

    tags = [
        "tasks",
        "workflow",
        "orchestration"
    ]

    capabilities = [
        "schedule_tasks"
    ]


    def __init__(
        self,
        base_path: str = "tasks"
    ):
        self.base_path = Path(base_path)


    def run(self) -> Optional[Task]:

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


        task_map = {
            task.id: task
            for task in tasks
        }


        for task in tasks:

            if task.status != "pending":
                continue


            dependencies = (
                task.metadata.get(
                    "dependencies",
                    []
                )
            )


            if all(
                task_map[d].status == "done"
                for d in dependencies
                if d in task_map
            ):
                return task


        return None