import subprocess
from typing import List, Type

from pydantic import BaseModel, Field
from Tools.Tool import Tool, ToolOutput
from Tools.tool_utils.ToolTag import ToolTag
from Tools.tool_utils.ToolCapability import ToolCapability


class CodeRunnerInput(BaseModel):
    command: list[str] = Field(
        ...,
        description="The executable command arguments split into a list array. Example: ['python', 'test.py']",
    )


class CodeRunnerOutput(ToolOutput):
    command: list[str]

    def to_string(self) -> str:
            result = super().to_string()
            
            if self.command:
                result += (
                    f"- Command: {self.command}\n"
                )
    
            return result


class CodeRunnerTool(Tool[CodeRunnerInput, CodeRunnerOutput]):
    name: str = "CodeRunnerTool"
    description: str = "Executes arbitrary terminal testing commands on the host machine safely."
    tags: list[ToolTag] = [ToolTag.DEVELOPMENT, ToolTag.TESTING]
    capabilities: list[ToolCapability] = [ToolCapability.EXECUTE_COMMANDS]
    path: str = "Tools/CodeRunnerTool.py"
    input_model: Type[CodeRunnerInput] = CodeRunnerInput
    output_model: Type[CodeRunnerOutput] = CodeRunnerOutput

    def run(self, input: CodeRunnerInput) -> CodeRunnerOutput:
        try:
            result = subprocess.run(
                input.command,
                capture_output=True,
                text=True
            )
        except Exception as e:
            return CodeRunnerOutput(
                command=input.command,
                success=False,
                message=f"Execution failed. \n Error: {e}"
            )
        message = ""
        success = True
        if result.stdout:
            message = result.stdout
        elif result.stderr:
            success = False
            message = result.stderr
        else:
            success = False
            message = "Command executed without failing. Neither stdout or stderr has content."

        return CodeRunnerOutput(
            command=input.command,
            success=success,
            message=message
        )




