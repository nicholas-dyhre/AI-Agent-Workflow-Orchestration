from typing import Type
from pydantic import BaseModel, Field, model_validator
from Tools.Tool import Tool, ToolOutput
from Tools.code.CodeUtils import CodeUtils
from Tools.tool_utils.ToolTag import ToolTag
from Tools.tool_utils.ToolCapability import ToolCapability

class PatchFileInput(BaseModel):
    paths: list[str] = Field(
        ...,
        description="Relative paths to files to patch",
    )
    search_string: list[str] = Field(
        ...,
        description="The string to search for in each file."
    )
    replace_string: list[str] = Field(
        ...,
        description="The string to replace the search string with in each file.",
    )

    @model_validator(mode="after")
    def validate_equal_lengths(self) -> "PatchFileInput":
        if len(self.paths) != len(self.search_string) != len(self.replace_string):
            raise ValueError(
                f"Mismatched array lengths. You provided {len(self.paths)} paths "
                f"but {len(self.search_string)} search_string and {len(self.replace_string)} replace_string. Every path must have corresponding search and replace strings."
            )
        return self

class PathFileOutput(ToolOutput):
    def to_string(self) -> str:
            return super().to_string()


class PatchFileTool(Tool[PatchFileInput, PathFileOutput]):
    name: str = "PatchFileTool"
    description: str = """Patches a file with new content. Input lists must be equal lengths."""
    tags: list[ToolTag] = [ToolTag.DEVELOPMENT, ToolTag.TESTING]
    capabilities: list[ToolCapability] = [ToolCapability.EXECUTE_COMMANDS, ToolCapability.CODE, ToolCapability.WRITE_FILES]
    path: str = "Tools/PatchFileTool.py"
    input_model: Type[PatchFileInput] = PatchFileInput
    output_model: Type[PathFileOutput] = PathFileOutput

    def run(self, input: PatchFileInput) -> PathFileOutput:
        try:
            responses: list[str] = []
            for sub_paths, search_string, replace_string in zip(input.paths, input.search_string, input.replace_string):
                if sub_paths is None:
                    sub_paths = "."
                isSuccess, response = CodeUtils.patch_file(sub_paths, search_string, replace_string)
                responses.append(response)
                if not isSuccess == True:
                    return PathFileOutput(
                        success=False,
                        message=f"Could not patch file(s) for paths '{input.paths}'. \n Responses: {'; '.join(responses)}. \n Error: {response}"
                    )
            return PathFileOutput(
                success=True,
                message="File(s) patched successfully. Responses: " + "; ".join(responses)
            )
        except Exception as e:
            return PathFileOutput(
                success=False,
                message=f"Could not patch file(s) for paths '{input.paths}'. \n Responses: {'; '.join(responses)}. \n Error: {str(e)}"
            )




