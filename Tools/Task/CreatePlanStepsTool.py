import uuid
from typing import Any, Optional, Type
from pydantic import BaseModel, Field, PrivateAttr
from Tools.Tool import Tool, ToolOutput
from Tools.models.ToolContextKey import ToolContextKey
from Tools.tool_utils.ToolTag import ToolTag
from Tools.tool_utils.ToolCapability import ToolCapability
from Tools.Task.TaskFileUtils import TaskFileUtils

class CreatePlanStepsInput(BaseModel):
    task_id: str = Field(
        ...,
        description="Writing the exact string '{{TASK_ID}}' will ensure infrastructure inserts correct taskid."
    )
    descriptions: list[str] = Field(
        ...,
        description="A list containing descriptions matching each corresponding title in the titles array."
    )


class CreatePlanStepsOutput(ToolOutput):
    created_plansteps: list[dict[str, Any]]
    created_count: int

    def to_string(self) -> str:
        result = super().to_string()
        result += (
            f"- Created Count: {self.created_count}\n"
        )
        if self.created_plansteps:
            result += "\nCreated planSteps:\n"
            for planstep in self.created_plansteps:
                result += f"  - ID: {planstep.get('id')} | Title: {planstep.get('description')}\n"
        return result


class CreatePlanStepsTool(Tool[CreatePlanStepsInput, CreatePlanStepsOutput]):
    name: str = "CreatePlanStepsTool"
    description: str = "Creates multiple structured plansteps simultaneously for a given Task."
    tags: list[ToolTag] = [ToolTag.TASKS, ToolTag.PERSISTENCE, ToolTag.FILESYSTEM]
    capabilities: list[ToolCapability] = [ToolCapability.WRITE_FILES, ToolCapability.CREATE_PLAN_STEP, ToolCapability.SAVE_TASKS, ToolCapability.UPDATE_TASKS, ToolCapability.MODIFY_TASKS]
    path: str = "Tools/CreateTasksTool.py"
    input_model: Type[CreatePlanStepsInput] = CreatePlanStepsInput
    output_model: Type[CreatePlanStepsOutput] = CreatePlanStepsOutput

    def run(self, input_data: CreatePlanStepsInput) -> CreatePlanStepsOutput:
        plan_steps_data = []

        for description in input_data.descriptions:
            task_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, description.strip()))
            
            plan_step_data = {
                "id": task_id,
                "description": description.strip()
            }

            plan_steps_data.append(plan_step_data)

        updates = {"plan": plan_steps_data}
            
        try:
            updated_task = TaskFileUtils.patch_task(input_data.task_id, updates)
        except Exception as e:
            return CreatePlanStepsOutput(
                success=False,
                created_plansteps=[],
                created_count=0,
                message=f"Failed to apply patch due to a data processing or schema error: {e}"
            )

        if isinstance(updated_task, str):
            return CreatePlanStepsOutput(
                success=False,
                created_plansteps=[],
                created_count=0,
                message=f"Failed to apply patch. Error: {updated_task}"
            )
        return CreatePlanStepsOutput(
            success=True,
            created_plansteps=plan_steps_data,
            created_count=len(plan_steps_data),
            message=f"Successfully created and persisted {len(plan_steps_data)} new task steps for task_id: {input_data.task_id}."
        )
