import subprocess
from typing import List
from Tools.Tool import Tool
from pydantic import BaseModel

class CreateBranchInput(BaseModel):
    branch_name: str


class CreateBranchTool(Tool):
    name: str = "create_branch"
    description: str = "Creates a new git branch"
    tags: List[str] = ["git", "branch"]
    path: str = "tools/git/create_branch.py"

    name = "create_branch"

    description = """Creates a new git branch"""

    tags = [
        "git",
        "github",
        "repository",
        "git branch"
    ]

    capabilities = [
        "create_branch",
        "external_repository_action"
    ]

    input_model = CreateBranchInput

    def run(self, input: CreateBranchInput) -> dict:
        result = subprocess.run(
            ["git", "checkout", "-b", input.branch_name],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            raise Exception(result.stderr.strip())
        
        return {
            "status": "success",
            "message": f"Branch '{input.branch_name}' created successfully.",
            "branch_name": input.branch_name,
            "stdout": result.stdout.strip()
        }
    