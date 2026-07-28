import json
from typing import Any, Generic, List, Protocol, Type, TypeVar
import typing
from pydantic import BaseModel, ConfigDict, Field

from Tools.models.ToolContextKey import ToolContextKey
from Tools.tool_utils.ToolTag import ToolTag
from Tools.tool_utils.ToolCapability import ToolCapability

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
    input: InputT
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
        print("Executing tool:", self.name)
        try:
            result = self.run(input_data)

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

    def format_for_llm(self) -> str:
        def simplify_type(t) -> str:
            if typing.get_origin(t) is typing.Union or str(t).startswith("typing.Union"):
                args = typing.get_args(t)
                non_none_args = [a for a in args if type(None) != a]
                base_str = " | ".join(simplify_type(a) for a in non_none_args)
                return f"{base_str} | None" if len(non_none_args) < len(args) else base_str

            origin = typing.get_origin(t)
            if origin is not None:
                args = typing.get_args(t)
                origin_name = origin.__name__
                args_str = ", ".join(simplify_type(a) for a in args)
                return f"{origin_name}[{args_str}]"

            try:
                return t.__name__
            except AttributeError:
                return str(t).replace("typing.", "")

        input_fields = []
        for name, field in self.input_model.model_fields.items():
            field_type = simplify_type(field.annotation)
            required = "required" if field.is_required() else "optional"
            desc = field.description or ""
            input_fields.append(f"- {name} ({field_type}, {required}): {desc}")

        output_fields = ["- success (bool)", "- message (str)"]
        for name, field in self.output_model.model_fields.items():
            if name in ["success", "message"]:
                continue
            field_type = simplify_type(field.annotation)
            output_fields.append(f"- {name} ({field_type})")

        return (
            f"tool_name: {self.name}\n"
            f"When to use:\n"
            f"{self._infer_usage_hint()}\n\n"
            f"Input:\n"
            f"{chr(10).join(input_fields)}\n\n"
            # f"Output:\n"
            # f"{chr(10).join(output_fields)}\n"
        )


    def _infer_usage_hint(self) -> str:
        return f"Use this tool when the task matches: {self.description.lower()}"

    def run(self, input_data: InputT) -> OutputT:
        raise NotImplementedError

    def initialize(self, context: dict[ToolContextKey, Any]) -> None: 
        pass

    def __call__(self, input_data: dict) -> ToolResult[OutputT]:

        if not input_data:
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