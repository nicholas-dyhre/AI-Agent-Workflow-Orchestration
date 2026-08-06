import json
import logging
from pathlib import Path
from typing import Any, ClassVar, Optional
import uuid

from Tasks.Task import AgentLog, PlanStep, Task
from Tasks.TaskState import State

logger = logging.getLogger(__name__)

class TaskFileUtils:
    _base_path: ClassVar[Optional[Path]] = None

    @classmethod
    def set_task_path(cls, path: str | Path) -> None:
        cls._base_path = Path(path)

    @classmethod
    def _get_configured_path(cls) -> Path:
        if cls._base_path is None:
            raise ValueError(
                "TaskFileUtils base path has not been configured. "
                "Call TaskFileUtils.set_base_path() before executing operations."
            )
        return cls._base_path

    @classmethod
    def get_task_file_path(cls, task_id: str) -> Path:
        return cls._get_configured_path() / f"{task_id}.json"

    @classmethod
    def load_task(cls, task_id: str) -> Task:
        path = cls.get_task_file_path(task_id)
        return cls.load_task_from_path(path)

    @classmethod
    def load_planstep(cls, task_id: str, plan_step_id: str) -> PlanStep:
        task = cls.load_task(task_id)
        plan_step = next((step for step in task.plan if step.id == plan_step_id), None)
        
        if plan_step is None:
            raise KeyError(f"PlanStep with ID '{plan_step_id}' not found in task '{task_id}'.")
            
        return plan_step

    @classmethod
    def load_task_from_path(cls, file_path: Path) -> Task:
        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
            task = Task(**data)
        except (json.JSONDecodeError, TypeError, KeyError, ValueError) as e:
            logger.error(f"Failed to read or parse task file {file_path.name}: {e}")
            raise RuntimeError(f"Failed to load task from {file_path.name}") from e

        message, valid = cls.validate_task(task)
        if not valid:
            logger.error(f"Task with id {task.id} is invalid: {message}")
            raise ValueError(f"Task with id {task.id} is invalid: {message}")
        return task

    @classmethod
    def load_all_tasks(cls) -> tuple[list[Task], list[str]]:
        path = cls._get_configured_path()
        tasks: list[Task] = []
        skipped_files: list[str] = []

        if not path.exists():
            return tasks, skipped_files

        for file in path.glob("*.json"):
            try:
                task = cls.load_task_from_path(file)
                tasks.append(task)
            except Exception as e:
                skipped_files.append(file.name)
                logger.warning(f"Skipping task file {file.name}: {e}")
        
        return tasks, skipped_files

    @classmethod
    def _override_task_file(cls, task: Task) -> Task:
        message, valid = cls.validate_task(task)
        if not valid:
            raise ValueError(message)
        
        path = cls.get_task_file_path(task.id)
        path.write_text(
            json.dumps(task.model_dump(mode="json"), indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        return task

    @classmethod
    def patch_task(cls, task_id: str, updates: dict[str, Any]) -> Task:
        task = cls.load_task(task_id)
        updated_task = task.model_copy(update=updates, deep=True)
        return cls._override_task_file(updated_task)

    @classmethod
    def patch_planstep_in_task_file(cls, task_id: str, plan_step_id: str, updates: dict[str, Any]) -> PlanStep: 
        task = cls.load_task(task_id)  
        
        step_index: Optional[int] = None
        plan_step: Optional[PlanStep] = None
        
        for idx, step in enumerate(task.plan):
            if step.id == plan_step_id:
                step_index = idx
                plan_step = step
                break
                
        if plan_step is None or step_index is None:
            raise KeyError(f"PlanStep with ID '{plan_step_id}' not found in task '{task_id}'.")

        updated_step = plan_step.model_copy(update=updates, deep=True)
        task.plan[step_index] = updated_step

        cls._override_task_file(task)
        return updated_step

    @classmethod
    def create_task_file(cls, task_data: dict[str, Any]) -> Task:
        if task_data.get("id") is None:
            task_data["id"] = str(uuid.uuid4())  # Generate a unique ID if not provided

        path = cls._get_configured_path()
        path.mkdir(parents=True, exist_ok=True)
        
        task = Task(**task_data)
        return cls._override_task_file(task)

    @classmethod
    def create_task(cls, task_data: dict[str, Any]) -> Task:
        return cls.create_task_file(task_data)

    @classmethod
    def advance_task_state(cls, task_id: str) -> Task:
        task = cls.load_task(task_id)
        state_list = list(State)
        current_index = state_list.index(task.status)
        
        if current_index + 1 < len(state_list):
            next_state =  state_list[current_index + 1]
            cls.patch_task(task_id, {"state": next_state.value})
            return cls.load_task(task_id)
        raise Exception(f"The state cannot be advanced beyond '{state_list[-1]}'")

    @classmethod
    def validate_task(cls, task: Task) -> tuple[str, bool]:
        if not task.id:
            return "Task validation failed: The property 'id' is missing or empty.", False
        if not task.title:
            return "Task validation failed: The property 'title' is missing or empty.", False
        if not task.description:
            return "Task validation failed: The property 'description' is missing or empty.", False
        if task.status is None:
            return "Task validation failed: The property 'status' is missing.", False
        return "Task is valid", True

    @classmethod
    def append_log_to_task(cls, task_id: str, log_entry: AgentLog) -> tuple[str, bool]:
        try:
            task = cls.load_task(task_id)
            task.logs.append(log_entry)
            cls._override_task_file(task)
            return "Log added successfully.", True
        except Exception as e:
            logger.error(f"Failed to append log to task {task_id}: {e}")
            return "Failed to append log to task.", False
