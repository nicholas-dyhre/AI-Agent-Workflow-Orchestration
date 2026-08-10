from typing import Type, List
from pydantic import BaseModel, Field
from Tools.Tool import Tool, ToolOutput
from Tools.code.CodeUtils import CodeUtils
from Tools.tool_utils.ToolTag import ToolTag
from Tools.tool_utils.ToolCapability import ToolCapability

class FileWriterRequest(BaseModel):
    sub_path: str = Field(
        ...,
        description="Relative path to file to write",
    )
    file_content: str = Field(
        ...,
        description="The content to be written to file."
    )

class FileWriterInput(BaseModel):
    files: List[FileWriterRequest] = Field(
        ...,
        description=(
            "List of files write requests. Each item contains a path and file content"
        )
    )

class FileWriterOutput(ToolOutput):
    files_written: List[str]
    files_not_written: List[tuple[str, str]]

    def to_string(self) -> str:
        result = super().to_string()

        for path in self.files_written:
            result += f"- file written: {path} \n"
        for path, error in self.files_not_written:
            result += f"- file not written: {path} | Error: {error} \n"
        return result

class FileWriterTool(Tool[FileWriterInput, FileWriterOutput]):
    name: str = "FileWriterTool"
    description: str = """Creates file. Writes to file. Overrides contents. USE TO CREATE CODE"""
    tags: List[ToolTag] = [ToolTag.DEVELOPMENT, ToolTag.FILESYSTEM, ToolTag.GENERATION]
    capabilities: List[ToolCapability] = [ToolCapability.GENERATE_CODE, ToolCapability.CODE, ToolCapability.WRITE_FILES]
    path: str = "Tools/code/FileWriterTool.py"
    input_model: Type[FileWriterInput] = FileWriterInput
    output_model: Type[FileWriterOutput] = FileWriterOutput

    def run(self, input_data: FileWriterInput) -> FileWriterOutput:
        try:
            files_written: List[str] = []
            files_not_written: List[tuple[str, str]] = []
            for file in input_data.files:
                issuccess, message = CodeUtils.write_file(file.sub_path, file.file_content)
                if issuccess:
                    files_written.append(file.sub_path)
                else:
                    files_not_written.append((file.sub_path, message))

            message = ""
            message += f"Files written {len(files_written)}" if len(files_written) else ""
            if message:
                message += " | " if message else ""
                message += f"files Not written {len(files_not_written)}" if len(files_not_written) else ""
            else:
                message += f"Files Not written {len(files_not_written)}"

            return FileWriterOutput(
                success=False if files_not_written else True,
                files_written=files_written,
                files_not_written=files_not_written,
                message=message
            )

        except Exception as e:
            return FileWriterOutput(
                success=False,
                files_written=[],
                files_not_written=[],
                message=f"Error: {str(e)}"
            )




