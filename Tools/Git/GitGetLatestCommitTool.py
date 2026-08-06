from typing import Type
from pydantic import BaseModel
from Tools.Tool import Tool, ToolOutput
from Tools.Git.GitUtils import GitUtils
from Tools.tool_utils.ToolTag import ToolTag
from Tools.tool_utils.ToolCapability import ToolCapability

class GitGetLatestCommitInput(BaseModel):
    pass

class GitGetLatestCommitOutput(ToolOutput):
    latest_commit_summary: str

    def to_string(self) -> str:
        return super().to_string() + f"- latest_commit_summary: {self.latest_commit_summary}\n"

class GitGetLatestCommitTool(Tool[GitGetLatestCommitInput, GitGetLatestCommitOutput]):
    name: str = "GitGetLatestCommitTool"
    description: str = "Returns the last tracking history log commit registration signature from the checked out branch HEAD tracking ledger."
    tags: list[ToolTag] = [ToolTag.GIT, ToolTag.UTILITY]
    path: str = "Tools/GitGetLatestCommitTool.py"
    capabilities: list[ToolCapability] = [ToolCapability.READ_FILES, ToolCapability.GIT_GET_REPO_INFO, ToolCapability.GIT]
    input_model: Type[GitGetLatestCommitInput] = GitGetLatestCommitInput
    output_model: Type[GitGetLatestCommitOutput] = GitGetLatestCommitOutput

    def run(self, input: GitGetLatestCommitInput) -> GitGetLatestCommitOutput:
        try:
            summary = GitUtils.get_latest_commit()
            return GitGetLatestCommitOutput(latest_commit_summary=summary, success=True, message="History ledger endpoint parsed.")
        except Exception as e:
            return GitGetLatestCommitOutput(latest_commit_summary="", success=False, message=str(e))
