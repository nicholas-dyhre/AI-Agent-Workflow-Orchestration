from typing import Type
from pydantic import BaseModel
from Tools.Git.GitUtils import GitUtils
from Tools.Tool import Tool, ToolOutput
from Tools.tool_utils.ToolTag import ToolTag
from Tools.tool_utils.ToolCapability import ToolCapability

class GetDiffInput(BaseModel):
    pass

class GetDiffOutput(ToolOutput):
    rich_diff_context: str

    def to_string(self) -> str:
        res = super().to_string()
        if self.rich_diff_context:
            res += f"- rich_diff_context:\n{self.rich_diff_context}\n"
        return res

class GetDiffTool(Tool[GetDiffInput, GetDiffOutput]):
    name: str = "GetDiffTool"
    description: str = "Returns a well-structured GitHub-style review diff with anchor lines context scopes to prevent code blindness."
    tags: list[ToolTag] = [ToolTag.DEVELOPMENT, ToolTag.GIT]
    capabilities: list[ToolCapability] = [ToolCapability.READ_FILES, ToolCapability.CODE]
    path: str = "Tools/code/GetDiffTool.py"
    input_model: Type[GetDiffInput] = GetDiffInput
    output_model: Type[GetDiffOutput] = GetDiffOutput

    def run(self, input_data: GetDiffInput) -> GetDiffOutput:
        try:
            diff_data = GitUtils.get_rich_contextual_diff()
            return GetDiffOutput(rich_diff_context=diff_data, success=True, message="Workspace modifications diff compiled.")
        except Exception as e:
            return GetDiffOutput(rich_diff_context="", success=False, message=f"Failed compiling structural code comparison diffs: {str(e)}")