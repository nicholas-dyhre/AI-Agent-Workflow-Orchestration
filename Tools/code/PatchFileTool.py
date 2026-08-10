from typing import Type
from pydantic import BaseModel, Field
from Tools.Tool import Tool, ToolOutput
from Tools.code.CodeUtils import CodeUtils
from Tools.tool_utils.ToolTag import ToolTag
from Tools.tool_utils.ToolCapability import ToolCapability

class PatchFileRequest(BaseModel):
    sub_path: str = Field(
        ...,
        description="Relative paths to files to patch",
    )
    search_string: str = Field(
        ...,
        description="The string to search for in each file."
    )
    replace_string: str = Field(
        ...,
        description="The string to replace the search string with in each file.",
    )

class PatchFileInput(BaseModel):
    files: list[PatchFileRequest] = Field(
        ...,
        description="List of file patch requests. Each item includes a file path, the search string to replace, and the replacement string.",
    )

class PathFileOutput(ToolOutput):
    def to_string(self) -> str:
            return super().to_string()

class PatchFileTool(Tool[PatchFileInput, PathFileOutput]):
    name: str = "PatchFileTool"
    description: str = """Patches an existing files content."""
    tags: list[ToolTag] = [ToolTag.DEVELOPMENT, ToolTag.TESTING]
    capabilities: list[ToolCapability] = [ToolCapability.EXECUTE_COMMANDS, ToolCapability.CODE, ToolCapability.WRITE_FILES]
    path: str = "Tools/code/PatchFileTool.py"
    input_model: Type[PatchFileInput] = PatchFileInput
    output_model: Type[PathFileOutput] = PathFileOutput

    def run(self, input_data: PatchFileInput) -> PathFileOutput:
        try:
            responses: list[str] = []
            for file in input_data.files:
                if file.sub_path is None:
                    return PathFileOutput(
                        success=False,
                        message=f"Can only patch files. sub_path cannot be null"
                    )
                isSuccess, response = CodeUtils.patch_file(file.sub_path, file.search_string, file.replace_string)
                responses.append(response)
                if not isSuccess == True:
                    return PathFileOutput(
                        success=False,
                        message=f"Could not patch file(s) for paths '{file.sub_path}'. \n Responses: {'; '.join(responses)}. \n Error: {response}"
                    )
            return PathFileOutput(
                success=True,
                message="File(s) patched successfully. Responses: " + "; ".join(responses)
            )
        except Exception as e:
            return PathFileOutput(
                success=False,
                message=f"Could not patch file(s) for paths '{file.sub_path}'. \n Responses: {'; '.join(responses)}. \n Error: {str(e)}"
            )




