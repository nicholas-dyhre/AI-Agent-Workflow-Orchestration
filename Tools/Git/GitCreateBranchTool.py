import subprocess
from typing import Type
from pydantic import BaseModel
from Tools.Git.GitUtils import GitUtils
from Tools.Tool import Tool, ToolOutput
from Tools.tool_utils.ToolTag import ToolTag
from Tools.tool_utils.ToolCapability import ToolCapability


class GitCreateBranchInput(BaseModel):
    branch_name: str


class GitCreateBranchOutput(ToolOutput):
    branch_name: str
    stdout: str

    def to_string(self) -> str:
        res = super().to_string()
        if self.branch_name:
            res += f"- Branch Name: {self.branch_name}\n"
        if self.stdout:
            res += f"- Output: {self.stdout}\n"
        return res


class GitCreateBranchTool(Tool[GitCreateBranchInput, GitCreateBranchOutput]):
    name: str = "CreateBranchTool"
    description: str = "Creates a new git branch."
    tags: list[ToolTag] = [ToolTag.GIT]
    capabilities: list[ToolCapability] = [ToolCapability.CREATE_BRANCH, ToolCapability.GIT]
    input_model: Type[GitCreateBranchInput] = GitCreateBranchInput
    output_model: Type[GitCreateBranchOutput] = GitCreateBranchOutput
    path: str = "Tools/Git/CreateBranchTool.py"

    def run(self, input_data: GitCreateBranchInput) -> GitCreateBranchOutput:
        try:
            GitUtils.create_branch(input_data.branch_name)
            return GitCreateBranchOutput(
                success=True,
                message=f"Branch '{input_data.branch_name}' created successfully.",
                branch_name=input_data.branch_name,
                stdout=""
            )
        except subprocess.CalledProcessError as e:
            return GitCreateBranchOutput(
                success=False,
                message=f"Branch '{input_data.branch_name}' could not be created. \n Error: {e.stderr.strip()}",
                branch_name=input_data.branch_name,
                stdout=e.stdout.strip()
            )