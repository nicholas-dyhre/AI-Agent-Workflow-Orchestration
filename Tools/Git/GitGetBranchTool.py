from typing import Type
from pydantic import BaseModel
from Tools.Tool import Tool, ToolOutput
from Tools.Git.GitUtils import GitUtils
from Tools.tool_utils.ToolTag import ToolTag
from Tools.tool_utils.ToolCapability import ToolCapability

class GitGetBranchInput(BaseModel):
    pass

class GitGetBranchOutput(ToolOutput):
    current_branch: str

    def to_string(self) -> str:
        return super().to_string() + f"- current_branch: {self.current_branch}\n"

class GitGetBranchTool(Tool[GitGetBranchInput, GitGetBranchOutput]):
    name: str = "GitGetBranchTool"
    description: str = "Returns the active git branch layout identity checked out currently."
    tags: list[ToolTag] = [ToolTag.GIT, ToolTag.UTILITY]
    capabilities: list[ToolCapability] = [ToolCapability.GIT_GET_REPO_INFO, ToolCapability.GIT]
    path: str = "Tools/GitGetBranchTool.py"
    input_model: Type[GitGetBranchInput] = GitGetBranchInput
    output_model: Type[GitGetBranchOutput] = GitGetBranchOutput

    def run(self, input_data: GitGetBranchInput) -> GitGetBranchOutput:
        try:
            branch = GitUtils.get_current_branch()
            return GitGetBranchOutput(current_branch=branch, success=not branch.startswith("Error"), message=f"Checked out branch: {branch}")
        except Exception as e:
            return GitGetBranchOutput(current_branch="", success=False, message=str(e))