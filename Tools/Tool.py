import json
from typing import Any, Generic, List, Type, TypeVar
import typing
from pydantic import BaseModel, ConfigDict

from Tools.models.ToolContextKey import ToolContextKey
from Tools.tool_utils.ToolTag import ToolTag
from Tools.tool_utils.ToolCapability import ToolCapability
from Common.color_printer import info

class ToolOutput(BaseModel):
    success: bool
    message: str
    def to_string(self) -> str: 
        return (
            f"- Success: {self.success}\n"
            f"- Message: {self.message}\n"
        )

InputT = TypeVar("InputT", bound=BaseModel)
OutputT = TypeVar("OutputT", bound=ToolOutput)

class ToolException(BaseModel, Generic[InputT]):
    tool: str
    input: InputT | dict[str, Any]
    error: str

    def to_string(self) -> str:
        return (
            f"- tool: {self.tool}\n"
            f"- input: {self.input}\n"
            f"- error: {self.error}"
        )

class ToolResult(BaseModel, Generic[OutputT]):
    data: OutputT | None = None
    error: ToolException[Any] | None = None

    def to_string(self) -> str:
        if self.data and self.data.success is True:
            return(
                f"- Data: {self.data.to_string()}"
            )
        else:
            if self.error:
                return (
                    f"- Error:\n"
                    f"{self.error.to_string()}"
                )
            return (
                f"- Error:\n" 
                f"Tool failed ungracefully"
            )

class Tool(BaseModel, Generic[InputT, OutputT]):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    name: str
    description: str
    tags: list[ToolTag]
    capabilities: List[ToolCapability]
    path: str
    input_model: Type[InputT]
    output_model: Type[OutputT]

    def describe(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_model.model_json_schema(),
            "output_schema": self.output_model.model_json_schema(),
            "tags": self.tags,
            "capabilities": self.capabilities,
        }

    def _simplify_schema(self) -> dict:
        schema = self.input_model.model_fields

        return {
            field_name: str(field.annotation)
            for field_name, field in schema.items()
        }

    def format_to_json(self) -> str:
        return json.dumps(
            self.describe(),
            indent=2
        )

    def execute(self, input_data: InputT) -> ToolResult[OutputT]:
        info(f"Executing tool: {self.name}")
        try:
            result = self.run(input_data)

            if result.success is not True:
                return ToolResult[OutputT](
                    data=result,
                    error=ToolException(
                        tool=self.name,
                        input = input_data,
                        error = result.message
                    )
                )

            return ToolResult[OutputT](
                data=result
            )

        except Exception as e:
            return ToolResult[OutputT](
                error=ToolException(
                    tool=self.name,
                    input=input_data,
                    error=str(e)
                )
            )

    def model_requires_input(self) -> bool:
        fields = self.input_model.model_fields
        if not fields:
            return False
        return any(field.is_required() for field in fields.values())

        
    # def format_for_llm(self) -> str:
    def __get_clean_type_name(self, t: Any) -> str:
        """Helper to extract clean string names for primitive types (e.g. str, int)."""
        if t is None or t is type(None):
            return "null"
        try:
            return str(t.__name__)
        except AttributeError:
            return str(t).replace("typing.", "")

    def __format_complex_type(self, annotation: type[Any] | None, indent_level: int) -> List[str]:
        """
        Recursively processes a type and returns a list of formatted string lines.
        Handles primitives, Generic Containers (lists/dicts), Unions, and Pydantic BaseModels.
        """
        pad = "  " * indent_level
        
        # 1. Handle Null / None types
        if annotation is None or annotation is type(None):
            return ["null"]

        origin = typing.get_origin(annotation)
        args = typing.get_args(annotation)

        # 2. Handle Pydantic BaseModel types directly
        if isinstance(annotation, type) and issubclass(annotation, BaseModel):
            lines: List[str] = ["{"]
            for sub_name, sub_field in annotation.model_fields.items():
                sub_req = "!" if sub_field.is_required() else "?"
                sub_desc = f" // {sub_field.description}" if sub_field.description else ""
                
                # Compute inner structure representation
                inner_lines = self.__format_complex_type(sub_field.annotation, indent_level + 1)
                
                if len(inner_lines) == 1:
                    lines.append(f"{pad}  \"{sub_name}\"{sub_req}: {inner_lines[0]}{sub_desc}")
                else:
                    # Multiline object nesting
                    lines.append(f"{pad}  \"{sub_name}\"{sub_req}: {inner_lines[0]}{sub_desc}")
                    lines.extend(inner_lines[1:])
            lines.append(f"{pad}" + "}")
            return lines

        # 3. Handle Union / Optional types (Type1 | Type2)
        if origin is typing.Union or str(annotation).startswith("typing.Union"):
            non_none_args = [a for a in args if a is not type(None)]
            union_parts: List[str] = []
            
            for arg in non_none_args:
                arg_lines = self.__format_complex_type(arg, indent_level)
                union_parts.append("\n".join(arg_lines))
            
            base_str = " | ".join(union_parts)
            return [f"{base_str} | null"] if len(non_none_args) < len(args) else [base_str]

        # 4. Handle Generic Containers like list[...] or dict[...]
        if origin is not None:
            origin_name = self.__get_clean_type_name(origin)
            if args:
                primary_arg = args[0]
                # Check if the collection wraps a complex BaseModel object
                # Also checks inner types inside standard collections (like list[FileReaderRequest])
                inner_origin = typing.get_origin(primary_arg)
                is_nested_model = (isinstance(primary_arg, type) and issubclass(primary_arg, BaseModel)) or \
                                    (inner_origin is not None and any(isinstance(a, type) and issubclass(a, BaseModel) for a in typing.get_args(primary_arg)))
                
                if is_nested_model:
                    # Output matching requested schema layout layout: list[ \n { ... } ]
                    child_lines = self.__format_complex_type(primary_arg, indent_level + 1)
                    header = f"{origin_name}["
                    footer = f"{pad}" + "}]"
                    
                    wrapped_lines = [header, f"{pad}  " + child_lines[0]]
                    wrapped_lines.extend(child_lines[1:-1])
                    wrapped_lines.append(footer)
                    return wrapped_lines
                else:
                    # Flat scalar list representations like list[str]
                    flat_args = ", ".join(self.__get_clean_type_name(a) for a in args)
                    return [f"{origin_name}[{flat_args}]"]
            
            return [origin_name]

        # 5. Default Fallback for native primitive types (str, int, float, bool)
        return [self.__get_clean_type_name(annotation)]
        
    def format_for_llm(self) -> str:
        # --- Main Execution Path Block for input parsing ---
        input_lines: List[str] = ["Input: {"]
        
        for name, field in self.input_model.model_fields.items():
            required_flag = "!" if field.is_required() else ""
            comment = f" //{field.description}" if field.description else ""
            
            # Generate lines for the field structure recursively
            field_lines = self.__format_complex_type(field.annotation, indent_level=1)
            
            if len(field_lines) == 1:
                input_lines.append(f"  \"{name}\"{required_flag}: {field_lines[0]}{comment}")
            else:
                # If block output spans multiple lines, integrate structural indent chains cleanly
                input_lines.append(f"  \"{name}\"{required_flag}: {field_lines[0]}{comment}")
                input_lines.extend(field_lines[1:])
                
        input_lines.append("}")

        return (
            f"tool_name: {self.name}\n"
            f"Tool_description: {self.description}\n"
            f"{chr(10).join(input_lines)}"
        )


    def _infer_usage_hint(self) -> str:
        return f"Use this tool when the task matches: {self.description.lower()}"

    def run(self, input_data: InputT) -> OutputT:
        raise NotImplementedError

    def initialize(self, context: dict[ToolContextKey, Any]) -> None: 
        pass

    def __call__(self, input_data: dict) -> ToolResult[OutputT]:

        if not input_data and self.model_requires_input():
            return ToolResult[OutputT](
                error=ToolException(
                    tool=self.name,
                    input={},
                    error="Missing input"
                )
            )

        try:
            validated = self.input_model(**input_data)
        except Exception as e:
            return ToolResult[OutputT](
                error=ToolException(
                    tool=self.name,
                    input=input_data,
                    error= (
                        f"Failed to validate input data \n"
                        f"input data: {input_data} \n" 
                        f"error: {e}"
                    )
                )
            )


        return self.execute(validated)