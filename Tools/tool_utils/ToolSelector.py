from __future__ import annotations

from Tools.Tool import Tool
from Tools.tool_utils.ToolRegistry import ToolRegistry
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Agent.BaseAgent import BaseAgent

class ToolSelector:
    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    def select(self, agent: BaseAgent):

        tools = {}

        for tool in self.registry.list().values():
            if self.is_allowed(agent, tool):
                tools[tool.name] = tool

        return tools

    def is_allowed(self, agent: BaseAgent, tool: Tool):

        # Explicit deny wins
        if any(capability in agent.denied_capabilities for capability in tool.capabilities):
            return False

        # Capability match
        capability_match = any(
            capability in agent.allowed_capabilities for capability in tool.capabilities
        )

        # Tag match
        tag_match = any(tag in agent.allowed_tags for tag in tool.tags)

        return capability_match and tag_match