from typing import Dict, List
from Agent.AgentNames import AgentName
from Tools.Tool import Tool
from Tools.tool_utils.ToolRegistry import ToolRegistry


class ToolSelector:
    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    def select(self, agent_name: AgentName) -> Dict[str, Tool]:
        match agent_name:
            case AgentName.DEVELOPER:
                tool_names = [
                "code_generator",
                "file_reader",
                "code_runner",
                "git_tool",
            ]
            case AgentName.REVIEWER:
                tool_names = [
                    "file_reader",
                    "diff_reader",
                ]
            case _: return {}

        tool_dict = self.buildToolDictionary(tool_names)
        self.require(tool_names, tool_dict)
        return tool_dict

    
    def buildToolDictionary(self, tool_names: List[str]) -> Dict[str, Tool]:
        tool_dict = {}
        for tool_name in tool_names:
            tool = self.registry.get(tool_name)
            tool_dict[tool_name] = tool

        return tool_dict

    def require(self, names: list[str], ToolDict: Dict[str, Tool]):
        missing = [n for n in names if n not in ToolDict]
        if missing:
            raise ValueError(f"Missing required tools: {missing}")
