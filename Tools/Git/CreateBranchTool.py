import subprocess
from typing import Type

from pydantic import BaseModel

from Tools.Tool import Tool, ToolOutput
from Tools.tool_utils.ToolTag import ToolTag
from Tools.tool_utils.ToolCapability import ToolCapability


class CreateBranchInput(BaseModel):
    branch_name: str


class CreateBranchOutput(ToolOutput):
    message: str
    branch_name: str
    stdout: str

    def to_string(self) -> str:
        return (
            f"- Status: {self.success}\n"
            f"- Branch Name: {self.branch_name}\n"
            f"- Message: {self.message}\n"
            f"- Output: {self.stdout}"
        )


class CreateBranchTool(Tool[CreateBranchInput, CreateBranchOutput]):
    name: str = "CreateBranchTool"
    description: str = "Creates a new git branch."
    tags: list[ToolTag] = [ToolTag.GIT]
    capabilities: list[ToolCapability] = [ToolCapability.CREATE_BRANCH]
    input_model: Type[CreateBranchInput] = CreateBranchInput
    output_model: Type[CreateBranchOutput] = CreateBranchOutput
    path: str = "Tools/Git/CreateBranchTool.py"

    def run(self, input: CreateBranchInput) -> CreateBranchOutput:
        try:
            result = subprocess.run(
                ["git", "checkout", "-b", input.branch_name],
                capture_output=True,
                text=True,
                timeout=10
            )
        except Exception as e:
            return CreateBranchOutput(
                success=False,
                message=f"Branch '{input.branch_name}' Could not be created. \n Error: {e}",
                branch_name=input.branch_name,
                stdout=""
            )

        if result.returncode != 0:
            raise Exception(result.stderr.strip())

        return CreateBranchOutput(
            success=True,
            message=f"Branch '{input.branch_name}' created successfully.",
            branch_name=input.branch_name,
            stdout=result.stdout.strip()
        )