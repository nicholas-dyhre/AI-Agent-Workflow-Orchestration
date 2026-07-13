from Tasks.Task import Task
from Tools.Tool import Tool

class ValidateTaskTool(Tool):

    name = "validate_task"

    description = """
    Validates that a task contains required fields.
    """

    tags = [
        "tasks",
        "validation"
    ]

    capabilities = [
        "validate_tasks"
    ]


    def run(
        self,
        task: Task
    ) -> dict:


        if not task.id:
            raise ValueError(
                "Missing task id"
            )


        if not task.title:
            raise ValueError(
                "Missing task title"
            )


        valid_states = [
            "pending",
            "in_progress",
            "done",
            "failed"
        ]


        if task.status not in valid_states:
            raise ValueError(
                f"Invalid status: {task.status}"
            )


        return {
            "valid": True,
            "task_id": task.id
        }