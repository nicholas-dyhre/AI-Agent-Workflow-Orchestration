from typing import Type
from pydantic import BaseModel, Field
from Tools.Git.GitUtils import GitUtils
from Tools.Tool import Tool, ToolOutput
from Tools.tool_utils.ToolTag import ToolTag
from Tools.tool_utils.ToolCapability import ToolCapability


class GitPushInput(BaseModel):
    branch_name: str | None = Field(
        ...,
        description="If not provided, the current checked out branch will be used. Default is null, and results in pushing to current branch."
    )
    remote_name: str | None = Field(
        ...,
        description="The target remote repository. Defaults to 'origin'."
    )


class GitPushOutput(ToolOutput):
    branch_name: str

    def to_string(self) -> str:
        return (super().to_string() +
            f"- Branch Name: {self.branch_name}\n"
        )


class GitPushTool(Tool[GitPushInput, GitPushOutput]):
    name: str = "GitPushTool"
    description: str = "Pushes local commits upstream to the remote repository branch."
    tags: list[ToolTag] = [ToolTag.GIT]
    capabilities: list[ToolCapability] = [ToolCapability.PUSH_CHANGES, ToolCapability.GIT]
    path: str = "Tools/Git/GitPushTool.py"
    input_model: Type[GitPushInput] = GitPushInput
    output_model: Type[GitPushOutput] = GitPushOutput

    def run(self, input_data: GitPushInput) -> GitPushOutput:
        try: 
            if not input_data.branch_name:
                input_data.branch_name = GitUtils.get_current_branch()
            if not input_data.remote_name:
                input_data.remote_name = "origin"
        except Exception as e:
            print(f"Failed to get current branch name. Error: {e}")
            return GitPushOutput(
                success=False,
                message=f"Failed to get current branch name. Error: {e}",
                branch_name=""
            )

        try:
            isSuccess, message = GitUtils.push_changes(input_data.branch_name)
            if isSuccess is True:
                return GitPushOutput(
                    success=True,
                    message=message,
                    branch_name=input_data.branch_name,
                )
            
            return GitPushOutput(
                success=False,
                message=message,
                branch_name=input_data.branch_name,
            )
        except Exception as e:
            return GitPushOutput(
                success=False,
                message=f"Pushing branch '{input_data.branch_name}' failed.\nError: {e}",
                branch_name=input_data.branch_name,
            )