import datetime
from typing import Type
from pydantic import BaseModel, Field
from Agent.AgentNames import AgentName
from Tasks.Task import AgentLog
from Tools.Tool import Tool, ToolOutput
from Tools.tool_utils.ToolTag import ToolTag
from Tools.tool_utils.ToolCapability import ToolCapability
from Tools.Task.TaskFileUtils import TaskFileUtils

class AppendTaskLogToolInput(BaseModel):
    agent_name: str = Field(
        "some_name",
        description="Inputs for this field will be overriden during runtime. Not required to be set when creating the tool input.",
    )
    task_id: str = Field(
        ...,
        description="Writing the exact string '{{TASK_ID}}' will ensure infrastructure inserts correct taskid."
    )
    log_entry_input: str = Field(
        ...,
        description="Describe the changes you made to the task, and any other relevant information. This will be stored in the task's log."
    )
    log_entry_output: str = Field(
        ...,
        description="Describe the effect these changes had on the task, and why these results improves the solution."
    )



class AppendTaskLogToolOutput(ToolOutput):
    task_id: str

    def to_string(self) -> str:
        result = super().to_string()
        result += (
            f"- Task ID: {self.task_id}"
        )
        return result


class AppendTaskLogTool(Tool[AppendTaskLogToolInput, AppendTaskLogToolOutput]):
    name: str = "AppendTaskLogTool"
    description: str = "Adds an agent execution log entry to a task."
    tags: list[ToolTag] = [ToolTag.TASKS, ToolTag.LOGGING, ToolTag.PERSISTENCE]
    capabilities: list[ToolCapability] = [ToolCapability.WRITE_TASK_LOGS]
    path: str = "Tools/AppendTaskLogTool.py"
    input_model: Type[AppendTaskLogToolInput] = AppendTaskLogToolInput
    output_model: Type[AppendTaskLogToolOutput] = AppendTaskLogToolOutput

    def run(self, input_data: AppendTaskLogToolInput) -> AppendTaskLogToolOutput:
        try:
            message, success = TaskFileUtils.append_log_to_task(input_data.task_id, AgentLog(
                agent=AgentName(input_data.agent_name),
                input=input_data.log_entry_input,
                output=input_data.log_entry_output,
                timestamp=datetime.datetime.now().isoformat()
            ))
        except Exception as e:
            return AppendTaskLogToolOutput(
                success=False,
                message=f"Could not append Task log. \n Error: {str(e)}",
                task_id=input_data.task_id,
            )

        if success is False:
            return AppendTaskLogToolOutput(
                success=False,
                message = f"Could not append Task log. \n Error: {message}",
                task_id = input_data.task_id,
            )
        else:
            return AppendTaskLogToolOutput(
                success=True,
                message = "Log added successfully",
                task_id = input_data.task_id,
            )