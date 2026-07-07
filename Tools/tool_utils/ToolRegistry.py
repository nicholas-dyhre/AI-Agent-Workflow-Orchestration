from typing import Dict
from Tools.Tool import Tool

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool):
        if tool.name in self._tools:
            raise ValueError(f"Tool already registered: {tool.name}")

        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        tool = self._tools.get(name)

        if not tool:
            raise ValueError(f"Tool not found in registry: {name}")

        return tool

    def list(self) -> Dict[str, Tool]:
        return self._tools