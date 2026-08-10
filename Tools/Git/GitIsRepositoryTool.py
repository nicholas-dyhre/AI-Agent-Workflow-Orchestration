from typing import Type
from pydantic import BaseModel
from Tools.Tool import Tool, ToolOutput
from Tools.Git.GitUtils import GitUtils
from Tools.tool_utils.ToolTag import ToolTag
from Tools.tool_utils.ToolCapability import ToolCapability

class GitIsRepositoryInput(BaseModel):
    pass

class GitIsRepositoryOutput(ToolOutput):
    is_git_tracked: bool

    def to_string(self) -> str:
        return super().to_string() + f"- is_git_tracked: {self.is_git_tracked}\n"

class GitIsRepositoryTool(Tool[GitIsRepositoryInput, GitIsRepositoryOutput]):
    name: str = "GitIsRepositoryTool"
    description: str = "Verifies if the workspace is actively tracked inside a functional Git architecture system."
    tags: list[ToolTag] = [ToolTag.GIT, ToolTag.UTILITY]
    capabilities: list[ToolCapability] = [ToolCapability.GIT_GET_REPO_INFO, ToolCapability.GIT, ToolCapability.RESTRCITED_UNTIL_FURTHER_CLARIFICATION]
    path: str = "Tools/GitIsRepositoryTool.py"
    input_model: Type[GitIsRepositoryInput] = GitIsRepositoryInput
    output_model: Type[GitIsRepositoryOutput] = GitIsRepositoryOutput

    def run(self, input_data: GitIsRepositoryInput) -> GitIsRepositoryOutput:
        try:
            tracked = GitUtils.is_repository()
            msg = "Active tracking Git system found." if tracked else "Directory currently untracked by Git."
            return GitIsRepositoryOutput(is_git_tracked=tracked, success=True, message=msg)
        except Exception as e:
            return GitIsRepositoryOutput(is_git_tracked=False, success=False, message=f"Git check error: {str(e)}")