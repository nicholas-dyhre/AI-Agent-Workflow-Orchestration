import json
from typing import List, Type
from pydantic import BaseModel, Field

from Agent.BaseAgent import BaseAgent

class ToolResult(BaseModel):
    success: bool
    message: str
    data: dict = Field(default_factory=dict)


class Tool(BaseModel):
    name: str
    description: str
    tags: List[str]
    capabilities: List[str]
    path: str
    input_model: Type[BaseModel]

    def describe(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_model.model_json_schema(),
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
        return json.dumps(self.describe(), indent=2)

    def execute(self, input_data: dict) -> ToolResult:
        try:
            validated_input = self.input_model(**input_data)
            result = self.run(validated_input)

            return ToolResult(success=True, message="OK", data=result or {})

        except Exception as e:
            return ToolResult(
                success=False,
                message=str(e),
                data={"tool": self.name, "input": input_data}
            )

    def run(self, input: BaseModel) -> dict:
        raise NotImplementedError

    def __call__(self, input_data: dict) -> ToolResult:
        return self.execute(input_data)
    
    