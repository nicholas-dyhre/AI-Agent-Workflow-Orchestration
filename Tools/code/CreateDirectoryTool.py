from typing import Type
from pydantic import BaseModel, Field
from Tools.Tool import Tool, ToolOutput
from Tools.code.CodeUtils import CodeUtils
from Tools.tool_utils.ToolTag import ToolTag
from Tools.tool_utils.ToolCapability import ToolCapability


class CreateDirectoryInput(BaseModel):
    paths: list[str | None] = Field(
        ...,
        description="Provide a list of subpaths with in the working directory, where new directories should be created.",
    )

class CreateDirectoryOutput(ToolOutput):
    created_directories: list[tuple[str, bool]]
    def to_string(self) -> str:
        result = super().to_string()
        for directory_response in self.created_directories:
            message, status = directory_response
            result += f"- Directory created: {status} | Message: {message}\n"
        return result


class CreateDirectoryTool(Tool[CreateDirectoryInput, CreateDirectoryOutput]):
    name: str = "CreateDirectoryTool"
    description: str = """Creates a directory at the specified path"""
    tags: list[ToolTag] = [ToolTag.DEVELOPMENT, ToolTag.TESTING]
    capabilities: list[ToolCapability] = [ToolCapability.EXECUTE_COMMANDS, ToolCapability.CODE, ToolCapability.WRITE_FILES]
    path: str = "Tools/CreateDirectoryTool.py"
    input_model: Type[CreateDirectoryInput] = CreateDirectoryInput
    output_model: Type[CreateDirectoryOutput] = CreateDirectoryOutput

    def run(self, input: CreateDirectoryInput) -> CreateDirectoryOutput:
        try:
            responses: list[tuple[str, bool]] = []
            for sub_path in input.paths:
                if sub_path is None:
                    responses.append(("", False))
                    continue
                isSuccess, response = CodeUtils.create_directory(sub_path)
                responses.append((response, isSuccess))
            return CreateDirectoryOutput(
                created_directories = responses,
                success=True,
                message="Directory creation completed without errors."
            )
        except Exception as e:
            return CreateDirectoryOutput(
                created_directories = [],
                success=False,
                message=f"Directory encountered a problem and did not complete for paths '{input.paths}'. \n Error: {str(e)}"
            )




