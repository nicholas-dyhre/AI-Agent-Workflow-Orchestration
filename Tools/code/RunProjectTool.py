from typing import Type, Optional
from pydantic import BaseModel, Field
from Tools.Tool import Tool, ToolOutput
from Tools.code.CodeUtils import CodeUtils
from Tools.tool_utils.ExecutableProjectCommand import ProjectRunOutput
from Tools.tool_utils.ToolTag import ToolTag
from Tools.tool_utils.ToolCapability import ToolCapability

class RunProjectInput(BaseModel):
    sub_path: Optional[str] = Field(
        None, description="Optional specific project component to run. If None, the tool will auto-discover and launch all detected runnable projects (e.g. backend and frontend simultaneously)."
    )

class RunProjectOutput(ToolOutput):
    execution_summary: str

    def to_string(self) -> str:
        res = super().to_string()
        if self.execution_summary:
            res += f"- execution_summary:\n{self.execution_summary}\n"
        return res

class RunProjectTool(Tool[RunProjectInput, RunProjectOutput]):
    name: str = "RunProjectTool"
    description: str = "Auto-detects code stacks and safely executes projects in the background without blocking execution threads."
    tags: list[ToolTag] = [ToolTag.DEVELOPMENT, ToolTag.UTILITY]
    capabilities: list[ToolCapability] = [ToolCapability.EXECUTE_COMMANDS, ToolCapability.CODE] # Map to your execution enum
    path: str = "Tools/RunProjectTool.py"
    input_model: Type[RunProjectInput] = RunProjectInput
    output_model: Type[RunProjectOutput] = RunProjectOutput

    def run(self, input: RunProjectInput) -> RunProjectOutput:
        try:
            outputs: list[ProjectRunOutput] = CodeUtils.run_project(relative_dir=input.sub_path)
            _message = ""
            _summary = ""
            for output in outputs:
                message, summary = output.summarize()
                _message += message
                _summary += summary
                    
            return RunProjectOutput(execution_summary=_summary, success=True, message=_message)
        except Exception as e:
            return RunProjectOutput(execution_summary="", success=False, message=f"Runtime launch execution crashed: {str(e)}")
