from typing import Any, Type
from pydantic import BaseModel, Field, model_validator
import pydantic_core
from Tools.Tool import Tool, ToolOutput
from Tools.code.CodeUtils import CodeUtils
from Tools.code.CodeUtils import CodeUtils
from Tools.tool_utils.ToolTag import ToolTag
from Tools.tool_utils.ToolCapability import ToolCapability


class ListFilesInput(BaseModel):
    sub_path: str | None = Field(
        ...,
        description="Relative paths to directory to list files. Defaults to project root if null.",
    )

    @model_validator(mode="before")
    @classmethod
    def handle_invalid_or_null_inputs(cls, data: dict[str, Any]) -> Any:
        for field_name, field_info in cls.model_fields.items():
            if field_info.default is not pydantic_core.PydanticUndefined:
                val = data.get(field_name)
                
                is_null_like = val is None or str(val).strip().lower() in ("null", "void", "none")
                is_wrong_type = val is not None and not isinstance(val, field_info.annotation) # type: ignore
                if is_null_like or is_wrong_type:
                    data[field_name] = field_info.default
                        
        return data


class ListFilesOutput(ToolOutput):
    file_tree_formatted: str

    def to_string(self) -> str:
        result = super().to_string()
        
        if self.file_tree_formatted:
            result += (
                f"\n - file_tree_formatted:\n{self.file_tree_formatted}"
            )

        return result


class ListFilesTool(Tool[ListFilesInput, ListFilesOutput]):
    name: str = "ListFilesTool"
    description: str = (
        "Lists folders and files in the specified directory path."
    )
    tags: list[ToolTag] = [ToolTag.FILESYSTEM, ToolTag.UTILITY]
    capabilities: list[ToolCapability] = [ToolCapability.READ_FILES, ToolCapability.CODE]
    path: str = "Tools/code/ListFilesTool.py"
    input_model: Type[ListFilesInput] = ListFilesInput
    output_model: Type[ListFilesOutput] = ListFilesOutput

    def run(self, input_data: ListFilesInput) -> ListFilesOutput:
        
        try:
            folders_to_skip: list[str] = ['Tasks']
            subpath = None if input_data.sub_path in [".", "/", "null", "None", None] else input_data.sub_path
            success, output = CodeUtils.list_files(sub_path=subpath, max_depth=3, folders_to_skip = folders_to_skip)
            return ListFilesOutput(
                file_tree_formatted=output if success else "",
                success=success,
                message=f"File tree for path '{input_data.sub_path}' generated successfully." if success else output
            )

        except Exception as e:
            return ListFilesOutput(
                file_tree_formatted="",
                success=False,
                message=f"Could not build file tree for path '{input_data.sub_path}'. \n Error: {str(e)}"
            )