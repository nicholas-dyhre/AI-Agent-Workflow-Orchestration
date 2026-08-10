from typing import Type
from pydantic import BaseModel, Field
from Tools.Git.GitUtils import GitUtils
from Tools.Tool import Tool, ToolOutput
from Tools.tool_utils.ToolTag import ToolTag
from Tools.tool_utils.ToolCapability import ToolCapability


class GitCreatePullRequestInput(BaseModel):
    is_draft: bool | None = Field(
        ...,
        description="Indicates whether the pull request should be created as a draft. Defaults to False"
    )
    pr_title: str = Field(
        ...,
        description="Title for the pull request."
    )
    pr_body: str = Field(
        ...,
        description="Comprehensive explanation detailing code structure modifications."
    )

class GitCreatePullRequestOutput(ToolOutput):
    branch_name: str

    def to_string(self) -> str:
        result = super().to_string()
        return result + (
            f"- Branch: {self.branch_name}\n"
        )

class GitCreatePullRequestTool(Tool[GitCreatePullRequestInput, GitCreatePullRequestOutput]):
    name: str = "GitCreatePullRequestTool"
    description: str = "Pushes localized branch updates upstream and instantiates a GitHub pull request using the GH CLI."
    tags: list[ToolTag] = [ToolTag.GIT]
    capabilities: list[ToolCapability] = [ToolCapability.CREATE_PULL_REQUEST, ToolCapability.GIT]
    path: str = "Tools/Git/GitCreatePullRequestTool.py"
    input_model: Type[GitCreatePullRequestInput] = GitCreatePullRequestInput
    output_model: Type[GitCreatePullRequestOutput] = GitCreatePullRequestOutput

    def run(self, input_data: GitCreatePullRequestInput) -> GitCreatePullRequestOutput:
        try:
            isSuccess, message = GitUtils.create_pull_request(
                title=input_data.pr_title,
                body=input_data.pr_body,
                draft=input_data.is_draft if input_data.is_draft else False
            )
            if isSuccess is True:
                return GitCreatePullRequestOutput(
                    success=True,
                    message="Pull request created successfully.",
                    branch_name=GitUtils.get_current_branch()
                )
            return GitCreatePullRequestOutput(
                success=False,
                message=f"Pull request creation failed. \n Error: {message}",
                branch_name=GitUtils.get_current_branch()
            )
        except Exception as e:
            return GitCreatePullRequestOutput(
                success=False,
                message=f"Pull request creation failed. \n Error: {e}",
                branch_name=GitUtils.get_current_branch()
            )