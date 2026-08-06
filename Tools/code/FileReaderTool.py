from pathlib import Path
from typing import List, Type

from pydantic import BaseModel, Field, model_validator
from Tools.Tool import Tool, ToolOutput
from Tools.code.CodeUtils import CodeUtils
from Tools.tool_utils.ToolTag import ToolTag
from Tools.tool_utils.ToolCapability import ToolCapability


class FileReaderInput(BaseModel):
    paths: List[str] = Field(
        ...,
        description="Relative path to the file(s) to read. If no relative sub path is provided, it defaults to the project root directory."
    )
    start_lines: List[int | None] = Field(
        ...,
        description="Line number to start reading from. If not provided, it defaults to the first line of the file. If 'None' is provided, it defaults to the first line of the file."
    )
    end_lines: List[int | None] = Field(
        ...,
        description="Line number to stop reading at. If not provided, it defaults to the last line of the file. If 'None' is provided, it defaults to the last line of the file."
    )

    @model_validator(mode="after")
    def validate_equal_lengths(self) -> "FileReaderInput":
        if len(self.paths) != len(self.start_lines) != len(self.end_lines):
            raise ValueError(
                f"Mismatched array lengths. You provided {len(self.paths)} paths "
                f"but {len(self.start_lines)} start lines and {len(self.end_lines)} end lines. Every path must have corresponding start and end line numbers."
            )
        return self


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
        "Opens targeted local disk filesystem resources and "
        "yields complete raw file data structures. Input lists must be equal lengths."
    )
    tags: list[ToolTag] = [ToolTag.FILESYSTEM, ToolTag.UTILITY]
    capabilities: list[ToolCapability] = [ToolCapability.READ_FILES, ToolCapability.CODE]
    path: str = "Tools/FileReaderTool.py"
    input_model: Type[FileReaderInput] = FileReaderInput
    output_model: Type[FileReaderOutput] = FileReaderOutput

    def run(self, input: FileReaderInput) -> FileReaderOutput:
        
        try:
            result: list[str] = []
            for path, start_line, end_line in zip(input.paths, input.start_lines, input.end_lines):
                file_content = CodeUtils.read_file(path, start_line, end_line)
                file_extension = Path(path).suffix.lstrip('.') or 'text'
                formatted_output = self.format_output(path, file_content, file_extension)
                result.append(formatted_output)
            return FileReaderOutput(
                formatted_output="\n".join(result), 
                success=True, 
                message="File(s) read successfully."
            )
        except Exception as e:
            return FileReaderOutput(
                formatted_output="",
                success=False,
                message=f"Could not build file tree for paths '{input.paths}'. \n Error: {str(e)}"
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