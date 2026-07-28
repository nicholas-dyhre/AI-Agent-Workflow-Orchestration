from pathlib import Path
from typing import Type

from pydantic import BaseModel, Field

from Tools.Tool import Tool, ToolOutput
from Tools.tool_utils.ToolTag import ToolTag
from Tools.tool_utils.ToolCapability import ToolCapability


class CodeGenInput(BaseModel):
    file_path: str = Field(
        ...,
        description="The relative destination path where the file should be saved (e.g., 'src/utils.py', 'index.js')."
    )
    content: str = Field(
        ...,
        description="The complete source code string payload that needs to be written to the file."
    )


class CodeGenOutput(ToolOutput):
    file_written: str
    extension_type: str
    bytes_saved: int

    def to_string(self) -> str:
        result = super().to_string()
        
        if self.file_written:
            result += (
                f"- file written: {self.file_written}\n"
            )
        if self.extension_type:
            result += (
                f"- Extension type: {self.extension_type}\n"
            )
        if self.bytes_saved:
            result += (
                f"- Bytes saved: {self.bytes_saved}\n"
            )

        return result


class CodeGeneratorTool(Tool[CodeGenInput, CodeGenOutput]):
    name: str = "CodeGeneratorTool"
    description: str = "Writes or overwrites complete source code files directly to the filesystem with the appropriate language extension."
    tags: list[ToolTag] = [ToolTag.DEVELOPMENT, ToolTag.FILESYSTEM, ToolTag.GENERATION]
    capabilities: list[ToolCapability] = [ToolCapability.WRITE_FILES, ToolCapability.GENERATE_CODE]
    path: str = "Tools/CodeGeneratorTool.py"
    input_model: Type[CodeGenInput] = CodeGenInput
    output_model: Type[CodeGenOutput] = CodeGenOutput

    def run(self, input: CodeGenInput) -> CodeGenOutput:
        try:
            target_path = Path(input.file_path)

            if target_path.parent:
                target_path.parent.mkdir(parents=True, exist_ok=True)

            file_extension = target_path.suffix.lower()

            if not file_extension:
                return CodeGenOutput(
                    success=False,
                    file_written=str(target_path),
                    extension_type=file_extension,
                    bytes_saved=len(input.content.encode("utf-8")),
                    message=f"The provided file_path '{input.file_path}' is missing a valid code type extension."
                )

            target_path.write_text(input.content, encoding="utf-8")

        except Exception as e:
            return CodeGenOutput(
                success=False,
                file_written=str(target_path),
                extension_type=file_extension,
                bytes_saved=len(input.content.encode("utf-8")),
                message=f"Code generation failed. \n Error: {e}"
            )

        return CodeGenOutput(
            success=True,
            file_written=str(target_path),
            extension_type=file_extension,
            bytes_saved=len(input.content.encode("utf-8")),
            message=f"Successfully created/updated code file at path: {target_path}"
        )
