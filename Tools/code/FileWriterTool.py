from typing import Type
from pydantic import BaseModel, Field, model_validator
from Tools.Tool import Tool, ToolOutput
from Tools.code.CodeUtils import CodeUtils
from Tools.tool_utils.ToolTag import ToolTag
from Tools.tool_utils.ToolCapability import ToolCapability


class FileWriterInput(BaseModel):
    paths: list[str | None] = Field(
        ...,
        description="List files in the specified directory path. If no relative sub path is provided, it defaults to the project root directory.",
    )
    file_contents: list[str] = Field(
        ...,
        description="The content to be written to each file."
    )

    @model_validator(mode="after")
    def validate_equal_lengths(self) -> "FileWriterInput":
        if len(self.paths) != len(self.file_contents):
            raise ValueError(
                f"Mismatched array lengths. You provided {len(self.paths)} paths "
                f"but {len(self.file_contents)} file_contents. Every path must have corresponding file content."
            )
        return self

class FileWriterOutput(ToolOutput):
    def to_string(self) -> str:
            return super().to_string()


class FileWriterTool(Tool[FileWriterInput, FileWriterOutput]):
    name: str = "FileWriterTool"
    description: str = """Overwrites or creates a file with complete content. Input lists must be equal lengths."""
    tags: list[ToolTag] = [ToolTag.DEVELOPMENT, ToolTag.TESTING]
    capabilities: list[ToolCapability] = [ToolCapability.EXECUTE_COMMANDS, ToolCapability.CODE, ToolCapability.WRITE_FILES]
    path: str = "Tools/FileWriterTool.py"
    input_model: Type[FileWriterInput] = FileWriterInput
    output_model: Type[FileWriterOutput] = FileWriterOutput

    def run(self, input: FileWriterInput) -> FileWriterOutput:
        try:
            responses: list[str] = []
            for sub_paths, file_contents in zip(input.paths, input.file_contents):
                if sub_paths is None:
                    sub_paths = "."
                isSuccess, response = CodeUtils.write_file(sub_paths, file_contents)
                if not isSuccess == True:
                    return FileWriterOutput(
                        success=False,
                        message=f"Could not write to file(s) for paths '{input.paths}'. \n Responses: {'; '.join(responses)}. \n Error: {response}"
                    )
                responses.append(response)
            return FileWriterOutput(
                success=True,
                message="File(s) written successfully. Responses: " + "; ".join(responses)
            )
        except Exception as e:
            return FileWriterOutput(
                success=False,
                message=f"Could not write to file(s) for paths '{input.paths}'. \n Responses: {'; '.join(responses)}. \n Error: {str(e)}"
            )




