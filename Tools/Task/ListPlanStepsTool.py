from pathlib import Path
from typing import Any, Optional, Type

from pydantic import BaseModel, Field, PrivateAttr

from Tasks.Task import PlanStep, Task
from Tools.Tool import Tool, ToolOutput
from Tools.models.ToolContextKey import ToolContextKey
from Tools.tool_utils.ToolTag import ToolTag
from Tools.tool_utils.ToolCapability import ToolCapability
from Tools.Task.TaskFileUtils import TaskFileUtils


class ListPlanStepsInput(BaseModel):
    task_id: str = Field(
        ...,
        description="Writing the exact string '{{TASK_ID}}' will ensure infrastructure inserts correct taskid."
    )

class ListPlanStepsOutput(ToolOutput):
    planSteps: list[PlanStep]
    task_count: int

    def to_string(self) -> str:
        result = super().to_string()
        result += (
            f"- Task Count: {self.task_count}\n"
        )

        if self.planSteps:
            result += "\nPlan Steps:\n"
            for step in self.planSteps:
                result += (
                    f" - id: {step.id}"
                    f"- name: {step.description}"
                    f"- status: ({step.status.value})"
                )

        return result


class ListPlanStepsTool(Tool[ListPlanStepsInput, ListPlanStepsOutput]):
    name: str = "ListPlanStepsTool"
    description: str = "Scans a specific task and retrieves a structured list of all currently saved plan steps."
    tags: list[ToolTag] = [ToolTag.TASKS, ToolTag.PERSISTENCE, ToolTag.QUERY]
    capabilities: list[ToolCapability] = [ToolCapability.READ_PLAN_STEPS]
    path: str = "Tools/ListPlanStepsTool.py"
    input_model: Type[ListPlanStepsInput] = ListPlanStepsInput
    output_model: Type[ListPlanStepsOutput] = ListPlanStepsOutput

    def run(self, input_data: ListPlanStepsInput) -> ListPlanStepsOutput:

        try:
            task: Task = TaskFileUtils.load_task(input_data.task_id)
            plan_steps = task.plan
            return ListPlanStepsOutput(
                success=True,
                planSteps=plan_steps,
                task_count=len(plan_steps),
                message=f"Plan steps successfully loaded for task with id {input_data.task_id}."
            )
        except Exception as e:
            return ListPlanStepsOutput(
                success=False,
                planSteps=[],
                task_count=0,
                message=f"Failed to load task with id {input_data.task_id}: {str(e)}"
            )