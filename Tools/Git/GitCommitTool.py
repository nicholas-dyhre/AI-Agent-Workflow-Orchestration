from typing import Type
from pydantic import BaseModel, Field
from Tools.Git.GitUtils import GitUtils
from Tools.Tool import Tool, ToolOutput
from Tools.tool_utils.ToolTag import ToolTag
from Tools.tool_utils.ToolCapability import ToolCapability

class GitCommitInput(BaseModel):
    commit_message: str = Field(
        ...,
        description="The descriptive message for the git commit explaining the changes."
    )

class GitCommitOutput(ToolOutput):
    message: str
    stdout: str

    def to_string(self) -> str:
        return (
            f"- Status: {self.success}\n"
            f"- Message: {self.message}\n"
            f"- Output: {self.stdout}"
        )

class GitCommitTool(Tool[GitCommitInput, GitCommitOutput]):
    name: str = "GitCommitTool"
    description: str = "Stages all current modifications and creates a local git commit."
    tags: list[ToolTag] = [ToolTag.GIT]
    capabilities: list[ToolCapability] = [ToolCapability.COMMIT_CHANGES, ToolCapability.GIT]
    path: str = "Tools/Git/GitCommitTool.py"
    input_model: Type[GitCommitInput] = GitCommitInput
    output_model: Type[GitCommitOutput] = GitCommitOutput

    def run(self, input: GitCommitInput) -> GitCommitOutput:
        try:
            message = GitUtils.commit_changes(input.commit_message)
        except Exception as e:
            return GitCommitOutput(
                success=False,
                message=f"Git commit failed.\nError: {e}",
                stdout=getattr(e, "stderr", "") or ""
            )

        return GitCommitOutput(
            success=True,
            message="Changes staged and committed successfully.",
            stdout=message
        )
