from typing import Optional, Type
from pydantic import BaseModel, Field
from Tools.Tool import Tool, ToolOutput
from Tools.code.CodeUtils import CodeUtils
from Tools.tool_utils.ExecutableProjectCommand import ProjectRunOutput
from Tools.tool_utils.ToolTag import ToolTag
from Tools.tool_utils.ToolCapability import ToolCapability

class RunTestsInput(BaseModel):
    sub_path: Optional[str] = Field(
        None, description="Optional specific project component to run. If None, the tool will auto-discover and launch all detected runnable projects (e.g. backend and frontend simultaneously)."
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
    description: str = "Infers testing framework, runs suites, and returns token-efficient compressed failure stack traces."
    tags: list[ToolTag] = [ToolTag.TESTING, ToolTag.UTILITY]
    capabilities: list[ToolCapability] = [ToolCapability.RUN_TESTS, ToolCapability.CODE]
    path: str = "Tools/RunTestsTool.py"
    input_model: Type[RunTestsInput] = RunTestsInput
    output_model: Type[RunTestsOutput] = RunTestsOutput

    def run(self, input: RunTestsInput) -> RunTestsOutput:
        try:
            outputs: list[ProjectRunOutput] = CodeUtils.run_tests(relative_dir=input.sub_path)

            _message = ""
            _summary = ""
            _test_summary = ""
            for output in outputs:
                message, summary = output.summarize()
                test_summary = output.summarize_tests()
                _message += message
                _summary += summary
                _test_summary += test_summary

            if not _summary:
                _message = "No test output available. Likely because no tests exists"
            return RunTestsOutput(execution_summary=_summary, test_summary=_test_summary, success=True, message= _message)
        except Exception as e:
            return RunTestsOutput(execution_summary="", test_summary="", success=False, message=f"Runtime launch execution crashed: {str(e)}")