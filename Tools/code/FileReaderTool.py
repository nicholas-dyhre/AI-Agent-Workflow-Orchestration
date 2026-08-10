from pathlib import Path
from typing import List, Optional, Type
from pydantic import BaseModel, Field, model_validator
from Tools.Tool import Tool, ToolOutput
from Tools.code.CodeUtils import CodeUtils
from Tools.tool_utils.ToolTag import ToolTag
from Tools.tool_utils.ToolCapability import ToolCapability


class FileReaderRequest(BaseModel):
    path: str = Field(
         ...,
        description="Relative path to the file to read. Ensure the file suffix is added"
    )
    start_line: Optional[int | None] = Field(
        None,
        description="Line number to start reading from (inclusive). Defaults to start of file if null."
    )
    end_line: Optional[int | None] = Field(
        None,
        description="Line number to stop reading at (inclusive). Defaults to end of file if null."
    )

    @model_validator(mode="after")
    def validate_range(self) -> "FileReaderRequest":
        if self.start_line is not None and self.end_line is not None:
            if self.start_line > self.end_line:
                raise ValueError(
                    f"start_line ({self.start_line}) must be <= end_line ({self.end_line})"
                )
        return self

class FileReaderInput(BaseModel):
    files: List[FileReaderRequest] = Field(
        ...,
        description=(
            "List of file read requests. Each item contains a path and optional start/end line range"
        )
    )

class FileReaderOutput(ToolOutput):
    formatted_output: str

    def to_string(self) -> str:
        result = super().to_string()
        
        if self.formatted_output:
            result += (
                f"- formatted_output: {self.formatted_output}\n"
            )

        return result


class FileReaderTool(Tool[FileReaderInput, FileReaderOutput]):
    name: str = "FileReaderTool"
    description: str = (
        """Read files - Either full contents or partial. Requires file path. Avoid guessing by running the list files tool."""
    )
    tags: list[ToolTag] = [ToolTag.FILESYSTEM, ToolTag.UTILITY]
    capabilities: list[ToolCapability] = [ToolCapability.READ_FILES, ToolCapability.CODE]
    path: str = "Tools/code/FileReaderTool.py"
    input_model: Type[FileReaderInput] = FileReaderInput
    output_model: Type[FileReaderOutput] = FileReaderOutput

    def run(self, input_data: FileReaderInput) -> FileReaderOutput:
        try:
            result: list[str] = []
            error_messages: list[str] = []
            for file in input_data.files:
                issuccess, file_content = CodeUtils.read_file(file.path, file.start_line, file.end_line)
                if not issuccess:
                    error_messages.append(file_content)
                    continue

                file_extension = Path(file.path).suffix.lstrip('.') or 'text'
                formatted_output = self.format_output(file.path, file_content, file_extension)
                result.append(formatted_output)
            if result and error_messages: #Partial success
                return FileReaderOutput(
                    formatted_output="\n".join(result), 
                    success=True, 
                    message=("Partial success: \n File(s) read successfully:" + "\n - ".join(result) + "\nFile(s) not read:" + "\n - ".join(result))
                )
            if result: #Success
                return FileReaderOutput(
                    formatted_output="\n".join(result), 
                    success=True, 
                    message="File(s) read successfully."
                )
            if error_messages: #Failure
                return FileReaderOutput(
                    formatted_output="", 
                    success=False, 
                    message="\n - ".join(error_messages)
                )
            return FileReaderOutput(
                formatted_output="", 
                success=False, 
                message="No files loaded."
            )
            
        except Exception as e:
            return FileReaderOutput(
                formatted_output="",
                success=False,
                message=f"Something went wrong.\nError: {str(e)}"
            )

    def format_output(self, file_path: str,file_content: str, file_extension: str) -> str:
        return (
            "---\n"
            f"FILE: [{file_path}]\n"
            f"```{file_extension}\n"
            f"{file_content}\n"
            f"```\n"
            "---\n"
        )