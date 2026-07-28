import subprocess
from typing import Type

from pydantic import BaseModel

from Tools.Tool import Tool, ToolOutput
from Tools.tool_utils.ToolTag import ToolTag
from Tools.tool_utils.ToolCapability import ToolCapability


class GetFilesChangedInput(BaseModel):
    pass


class GetFilesChangedOutput(ToolOutput):
    files_changed: list[str]

    def to_string(self) -> str:
        return (
            f"- Files Changed:\n"
            + "\n".join(f"  - {file}" for file in self.files_changed)
        )


class GetFilesChangedTool(Tool[GetFilesChangedInput, GetFilesChangedOutput]):
    name: str = "GetFilesChangedTool"
    description: str = "Returns an itemized string array tracking file paths mutated within the active workspace."
    tags: list[ToolTag] = [ToolTag.GIT]
    capabilities: list[ToolCapability] = [ToolCapability.GET_CODE_CHANGES]
    path: str = "Tools/Git/GetFilesChangedTool.py"
    input_model: Type[GetFilesChangedInput] = GetFilesChangedInput
    output_model: Type[GetFilesChangedOutput] = GetFilesChangedOutput

    def run(self, input: GetFilesChangedInput) -> GetFilesChangedOutput:
        try: 
            result = subprocess.run(
                ["git", "diff", "--name-only"],
                capture_output=True,
                text=True,
                check=True
            )
        except Exception as e:
            return GetFilesChangedOutput(
                success = True,
                files_changed=[],
                message = f"Action failed. \n Error {e}"
            )

        return GetFilesChangedOutput(
            success = True,
            files_changed=[
                line.strip()
                for line in result.stdout.splitlines()
                if line.strip()
            ],
            message = "Action successful. \n Files changed \n"
        )