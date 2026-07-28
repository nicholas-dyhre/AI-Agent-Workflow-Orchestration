from typing import Dict, List
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
            raise ValueError(f"Tool not found: {name}")

        return tool

    def has(self, name: str) -> bool:
        return name in self._tools

    def list(self) -> Dict[str, Tool]:
        return self._tools

    def find_by_tags(self, tags: List[str]) -> List[Tool]:
        return [tool for tool in self._tools.values() if any(tag in tool.tags for tag in tags)]

    def require(self, names: List[str]):
        missing = [name for name in names if name not in self._tools]
        if missing:
            raise ValueError(f"Missing required tools in registry: {missing}")
