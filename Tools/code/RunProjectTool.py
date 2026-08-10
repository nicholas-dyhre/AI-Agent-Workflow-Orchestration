from typing import List, Type, Optional
from pydantic import BaseModel, Field
from Tools.Tool import Tool, ToolOutput
from Tools.code.CodeUtils import CodeUtils
from Tools.tool_utils.ExecutableProjectCommand import ProjectRunOutput
from Tools.tool_utils.ToolTag import ToolTag
from Tools.tool_utils.ToolCapability import ToolCapability

class RunProjectInput(BaseModel):
    sub_path: str | None = Field(
        ...,
        description="Relative paths to directory to execute run command. Defaults to project root.",
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
    description: str = "Run project tool. Tool infers run commands from files."
    tags: List[ToolTag] = [ToolTag.DEVELOPMENT, ToolTag.UTILITY]
    capabilities: List[ToolCapability] = [ToolCapability.EXECUTE_COMMANDS, ToolCapability.CODE]
    path: str = "Tools/code/RunProjectTool.py"
    input_model: Type[RunProjectInput] = RunProjectInput
    output_model: Type[RunProjectOutput] = RunProjectOutput

    def run(self, input_data: RunProjectInput) -> RunProjectOutput:
        try:
            subpath = None if input_data.sub_path in [".", "/", "null", "None", None] else input_data.sub_path
            outputs: List[ProjectRunOutput] = CodeUtils.run_project(relative_dir=input_data.sub_path)
            if not outputs:
                return RunProjectOutput(
                    execution_summary="", 
                    success=False, 
                    message="No output available. Likely because no project exist.")

            messages: List[str] = []
            summaries: List[str] = []
            for output in outputs:
                message, summary = output.summarize()
                messages.append(message)
                summaries.append(summary)
                    
            return RunProjectOutput(
                execution_summary=" ".join(summaries), 
                success=True if outputs else False, 
                message="\n".join(messages) if messages else "No output summery available. Likely because no project exist.")
        except Exception as e:
            return RunProjectOutput(execution_summary="", success=False, message=f"Runtime launch execution crashed: {str(e)}")
