from pathlib import Path
from typing import Type
from pydantic import BaseModel, Field
from Tools.Tool import Tool, ToolOutput
from Tools.code.CodeUtils import CodeUtils
from Tools.tool_utils.ToolTag import ToolTag
from Tools.tool_utils.ToolCapability import ToolCapability


class CreateDirectoryInput(BaseModel):
    sub_paths: list[str] = Field(
        ...,
        description="Creates a folder on paths"
    )

class CreateDirectoryOutput(ToolOutput):
    created_directories: list[tuple[str, bool]]
    def to_string(self) -> str:
        result = super().to_string()
        for directory_response in self.created_directories:
            message, status = directory_response
            result += f"- Directory created: {status} | Message: {message}\n"
        return result


class CreateFolderTool(Tool[CreateDirectoryInput, CreateDirectoryOutput]):
    name: str = "CreateFolderTool"
    description: str = """Folder creater tool"""
    tags: list[ToolTag] = [ToolTag.DEVELOPMENT, ToolTag.TESTING]
    capabilities: list[ToolCapability] = [ToolCapability.EXECUTE_COMMANDS, ToolCapability.CODE, ToolCapability.WRITE_FILES]
    path: str = "Tools/code/CreateFolderTool.py"
    input_model: Type[CreateDirectoryInput] = CreateDirectoryInput
    output_model: Type[CreateDirectoryOutput] = CreateDirectoryOutput

    def run(self, input_data: CreateDirectoryInput) -> CreateDirectoryOutput:
        try:
            responses: list[tuple[str, bool]] = []
            for sub_path in input_data.sub_paths:
                sub_path = str(Path(sub_path).with_suffix(''))
                isSuccess, response = CodeUtils.create_directory(sub_path)
                responses.append((response, isSuccess))
            return CreateDirectoryOutput(
                created_directories = responses,
                success=True,
                message="Tool terminated correctly"
            )
        except Exception as e:
            return CreateDirectoryOutput(
                created_directories = [],
                success=False,
                message=f"Directory encountered a problem and did not complete for paths '{input_data.sub_paths}'. \n Error: {str(e)}"
            )




