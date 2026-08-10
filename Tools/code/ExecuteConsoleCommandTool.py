import subprocess
import shlex
from typing import Optional, Type
from pydantic import BaseModel, Field
from Tools.Tool import Tool, ToolOutput
from Tools.code.CodeUtils import CodeUtils
from Tools.tool_utils.ToolCapability import ToolCapability
from Tools.tool_utils.ToolTag import ToolTag
from Common.color_printer import info

class ExecuteConsoleCommandInput(BaseModel):
    command: str = Field(
        ...,
        description=(
            "The exact bash or terminal command string to execute (e.g., 'ls -la')."
        )
    )
    sub_path: Optional[str | None] = Field(
        None,
        description="subpath to execute the command"
    )

class ExecuteConsoleCommandOutput(ToolOutput):
    exit_code: int

    def to_string(self) -> str:
        result = super().to_string()
        
        if self.exit_code:
            result += (
                f"- exit_code: {self.exit_code}\n"
            )

        return result
class ExecuteConsoleCommandTool(Tool[ExecuteConsoleCommandInput, ExecuteConsoleCommandOutput]):
    name: str = "ExecuteConsoleCommandTool"
    description: str = (
        """Request console command execution"""
    )
    tags: list[ToolTag] = [ToolTag.FILESYSTEM, ToolTag.UTILITY, ToolTag.DEVELOPMENT]
    capabilities: list[ToolCapability] = [ToolCapability.EXECUTE_COMMANDS, ToolCapability.CODE]
    path: str = "Tools/code/ExecuteConsoleCommandTool.py"
    input_model: Type[ExecuteConsoleCommandInput] = ExecuteConsoleCommandInput
    output_model: Type[ExecuteConsoleCommandOutput] = ExecuteConsoleCommandOutput

    def run(self, input_data: ExecuteConsoleCommandInput) -> ExecuteConsoleCommandOutput:
        """
        Executes a shell command locally after manual human approval.
        Accepts a single string command and returns stdout, stderr, and exit code.
        """
        # Blocklist
        blocklist = ["rm -rf /", "drop database", "mkfs", "dd"]
        if any(blocked in input_data.command.lower() for blocked in blocklist):
            return ExecuteConsoleCommandOutput(
                success = False,
                message = "Error: Command contains forbidden operations.",
                exit_code = 1
            )
        def getUserApproval() -> bool:
            info(f"[AGENT REQUESTING CONSOLE ACCESS]: {input_data.command}")
            user_approval = input("Allow execution? (y/n): ").strip().lower()
            print(f"DEBUG: user_approval value is -> [{user_approval}]") 
            print(f"is user_approval == 'y': {user_approval == 'y'}")
            print(f"is user_approval == '[y]': {user_approval == '[y]'}")
            print(f"is user_approval == 'n {user_approval == 'n'}")

            user_approval_checked: bool | None = user_approval in ['y', '[y]']
            if user_approval_checked == True:
                info(f"User approved execution.")
                return True
            user_approval_checked = False if user_approval in ['n', '[n]'] else None
            if user_approval_checked == False:
                info(f"User rejected execution.")
                return False
            info(f"Wrong input. Input was {user_approval}, but expected to be 'y' or 'N'.")
            return getUserApproval()


        
        # if user_approval not in ['y', '[y]']:
        approval = getUserApproval()
        if approval == False:
            return ExecuteConsoleCommandOutput(
                success = False,
                message = "Execution rejected by the user.",
                exit_code = 1
            )

        try:
            parsed_args = shlex.split(input_data.command)
            
            resultcode, stdout, stderr = CodeUtils.run_process(parsed_args, input_data.sub_path)
            message = f"\nstdout: {stdout}" if stdout else ""
            message += f"\n nstderr: {stderr}" if stdout else ""
            resultcode = resultcode if resultcode == 0 else 1

            return ExecuteConsoleCommandOutput(
                success = True if resultcode == 0 else False,
                message = f"Execution approved by the user. \nOutput: {message}",
                exit_code = resultcode
            )
            
        except subprocess.TimeoutExpired:
            return ExecuteConsoleCommandOutput(
                success = False,
                message = "Execution timed out after 30 seconds.",
                exit_code = 1
            )
        except Exception as e:
            return ExecuteConsoleCommandOutput(
                success = False,
                message = f"An error occurred during execution: {str(e)}",
                exit_code = 1
            )
