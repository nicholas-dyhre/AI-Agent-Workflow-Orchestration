from typing import Type
from pydantic import BaseModel, Field
from Tools.Tool import Tool, ToolOutput
from Tools.code.CodeUtils import CodeUtils
from Tools.tool_utils.ExecutableProjectCommand import ProjectRunOutput
from Tools.tool_utils.ToolTag import ToolTag
from Tools.tool_utils.ToolCapability import ToolCapability

class RunTestsInput(BaseModel):
    sub_path: str | None = Field(
        ..., description="If null, the tool will auto-discover and launch all detected runnable projects (e.g. backend and frontend simultaneously)."
    )

class RunTestsOutput(ToolOutput):
    execution_summary: str
    test_summary: str
    
    def to_string(self) -> str:
        res = super().to_string()
        if self.execution_summary:
            res += f"- execution_summary:\n{self.execution_summary}\n"
        return res

class RunTestsTool(Tool[RunTestsInput, RunTestsOutput]):
    name: str = "RunTestsTool"
    description: str = "Run tests tool. Tool infers run commands from files."
    tags: list[ToolTag] = [ToolTag.TESTING, ToolTag.UTILITY]
    capabilities: list[ToolCapability] = [ToolCapability.RUN_TESTS, ToolCapability.CODE]
    path: str = "Tools/code/RunTestsTool.py"
    input_model: Type[RunTestsInput] = RunTestsInput
    output_model: Type[RunTestsOutput] = RunTestsOutput

    def run(self, input_data: RunTestsInput) -> RunTestsOutput:
        try:
            subpath = None if input_data.sub_path in [".", "/", "null", "None", None] else input_data.sub_path
            outputs: list[ProjectRunOutput] = CodeUtils.run_tests(relative_dir=subpath)
            messages = []
            summaries = []
            test_summaries = []

            for output in outputs:
                message, summary = output.summarize()
                test_summary = output.summarize_tests()
                messages.append(message)
                summaries.append(summary)
                test_summaries.append(test_summary)

            return RunTestsOutput(
                execution_summary="\n".join(summaries) if len(summaries) else "No test output available. Likely because no tests exist.", 
                test_summary="\n".join(test_summaries), 
                success=True, 
                message= "\n".join(messages) if messages else "No test output available. Likely because no tests exist."
            )
        except Exception as e:
            return RunTestsOutput(execution_summary="", test_summary="", success=False, message=f"Runtime launch execution crashed: {str(e)}")