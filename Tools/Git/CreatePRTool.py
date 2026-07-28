import subprocess
from typing import Type

from pydantic import BaseModel, Field

from Tools.Tool import Tool, ToolOutput
from Tools.tool_utils.ToolTag import ToolTag
from Tools.tool_utils.ToolCapability import ToolCapability


class CreatePRInput(BaseModel):
    branch_name: str = Field(
        ...,
        description="Target git workspace feature branch containing your local code commits."
    )
    pr_title: str = Field(
        ...,
        description="Short explanatory pull request title statement."
    )
    pr_description: str = Field(
        ...,
        description="Comprehensive explanation detailing code structure modifications."
    )


class CreatePROutput(ToolOutput):
    message: str
    branch_name: str

    def to_string(self) -> str:
        return (
            f"- Status: {self.success}\n"
            f"- Branch: {self.branch_name}\n"
            f"- Message: {self.message}"
        )


class CreatePRTool(Tool[CreatePRInput, CreatePROutput]):
    name: str = "CreatePRTool"
    description: str = "Pushes localized branch updates upstream and instantiates a GitHub pull request using the GH CLI."
    tags: list[ToolTag] = [ToolTag.GIT]
    capabilities: list[ToolCapability] = [ToolCapability.CREATE_PULL_REQUEST]
    path: str = "Tools/Git/CreatePRTool.py"
    input_model: Type[CreatePRInput] = CreatePRInput
    output_model: Type[CreatePROutput] = CreatePROutput

    def run(self, input: CreatePRInput) -> CreatePROutput:
        try:
            subprocess.run(
                ["git", "checkout", input.branch_name],
                check=True
            )

            subprocess.run(
                ["git", "push", "origin", input.branch_name],
                check=True
            )

            subprocess.run(
                [
                    "gh",
                    "pr",
                    "create",
                    "--title",
                    input.pr_title,
                    "--body",
                    input.pr_description,
                    "--base",
                    "main",
                    "--head",
                    input.branch_name,
                ],
                check=True
            )
        except Exception as e:
            return CreatePROutput(
                success=False,
                message=f"The pull request creation failed. \n Error: {e}",
                branch_name=input.branch_name
            )

        return CreatePROutput(
            success=True,
            message=f"Pull request for branch '{input.branch_name}' created successfully.",
            branch_name=input.branch_name
        )