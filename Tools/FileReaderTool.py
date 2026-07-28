from pathlib import Path
from typing import List, Type

from pydantic import BaseModel, Field
from Tools.Tool import Tool, ToolOutput
from Tools.tool_utils.ToolTag import ToolTag
from Tools.tool_utils.ToolCapability import ToolCapability


class FileReaderInput(BaseModel):
    path: str = Field(
        ...,
        description="Relative file system project file path target location string."
    )


class FileReaderOutput(ToolOutput):
    path: str
    

    def to_string(self) -> str:
        result = super().to_string()
        
        if self.path:
            result += (
                f"- path: {self.path}\n"
            )

        return result


class FileReaderTool(Tool[FileReaderInput, FileReaderOutput]):
    name: str = "FileReaderTool"
    description: str = (
        "Opens targeted local disk filesystem resources and "
        "yields complete raw file data structures."
    )

    tags: list[ToolTag] = [ToolTag.FILESYSTEM, ToolTag.UTILITY]

    capabilities: list[ToolCapability] = [ToolCapability.READ_FILES]

    path: str = "Tools/FileReaderTool.py"

    input_model: Type[FileReaderInput] = FileReaderInput
    output_model: Type[FileReaderOutput] = FileReaderOutput

    def run(self, input: FileReaderInput) -> FileReaderOutput:
        file_path = Path(input.path)

        if not file_path.exists():
            return FileReaderOutput(
                path=input.path,
                success=False,
                message=f"Requested target path does not exist: {input.path}"
            )

        if not file_path.is_file():
            return FileReaderOutput(
                path=input.path,
                success=False,
                message=f"Requested path is not a file: {input.path}"
            )

        content = file_path.read_text(
            encoding="utf-8"
        )

        return FileReaderOutput(
            path=input.path,
            success=True,
            message=content
        )