import json
from pathlib import Path
from Tools.Tool import Tool

class AppendTaskLogTool(Tool):

    name = "append_task_log"

    description = """
    Adds an agent execution log entry to a task.
    """

    tags = [
        "tasks",
        "logging",
        "persistence"
    ]

    capabilities = [
        "write_task_logs"
    ]


    def __init__(
        self,
        base_path: str = "tasks"
    ):
        self.base_path = Path(base_path)


    def run(
        self,
        task_id: str,
        log_entry: dict
    ):


        file_path = (
            self.base_path /
            f"{task_id}.json"
        )


        if not file_path.exists():
            raise ValueError(
                f"Task not found: {task_id}"
            )


        data = json.loads(
            file_path.read_text()
        )


        data["logs"].append(
            log_entry
        )


        file_path.write_text(
            json.dumps(
                data,
                indent=2
            )
        )


        return {
            "status": "log_added",
            "task_id": task_id
        }