from typing import Any, Dict, Type
from pydantic import BaseModel, Field
from Tasks.Task import PlanStep
from Tools.Tool import Tool, ToolOutput
from Tools.tool_utils.ToolTag import ToolTag
from Tools.tool_utils.ToolCapability import ToolCapability
from Tools.Task.TaskFileUtils import TaskFileUtils


class PatchPlanStepInput(BaseModel):
    task_id: str = Field(
        ...,
        description="Writing the exact string '{{TASK_ID}}' will ensure infrastructure inserts correct taskid."
    )
    plan_step_id: str = Field(
        ...,
        description="Writing the exact id will ensure infrastructure finds the plan step"

    )
    updates: Dict[str, Any] = Field(
        ...,
        description="A key-value dictionary containing the fields to update (e.g., {'description': 'new description'})."
    )


class PatchPlanStepOutput(ToolOutput):
    task: PlanStep | None
    updated_fields: list[str]

    def to_string(self) -> str:
        result = super().to_string()
        
        if self.task and self.task.id:
            result += (
                f"- Task ID: {self.task.id}\n"
            )
        if self.updated_fields:
            result += (
                f"- Updated Fields: {', '.join(self.updated_fields)}\n"
            )
    
        return result


class PatchPlanStepTool(Tool[PatchPlanStepInput, PatchPlanStepOutput]):
    name: str = "PatchPlanStepTool"
    description: str = "Applies partial structural modifications (patches) to an existing stored planstep without overwriting unchanged fields."
    tags: list[ToolTag] = [ToolTag.TASKS, ToolTag.PERSISTENCE]
    capabilities: list[ToolCapability] = [ToolCapability.MODIFY_TASKS]
    path: str = "Tools/PatchPlanStepTool.py"
    input_model: Type[PatchPlanStepInput] = PatchPlanStepInput
    output_model: Type[PatchPlanStepOutput] = PatchPlanStepOutput

    def run(self, input_data: PatchPlanStepInput) -> PatchPlanStepOutput:
        
        try:
            updated_planstep = TaskFileUtils.patch_planstep_in_task_file(input_data.task_id, input_data.plan_step_id, input_data.updates)
        except Exception as e:
            return PatchPlanStepOutput(
                success = False,
                task=None,
                updated_fields=list(input_data.updates.keys()),
                message=f"Failed to apply patch due to a data processing or schema error: {e} \n"
            )

        if isinstance(updated_planstep, str):
            return PatchPlanStepOutput(
                success = False,
                task=None,
                updated_fields=list(input_data.updates.keys()),
                message=f"Failed to apply patch. Error: {updated_planstep} \n"
            )

        return PatchPlanStepOutput(
            success = True,
            task=updated_planstep,
            updated_fields=list(input_data.updates.keys()),
            message="Task successfully patched and persisted. \n"
        )