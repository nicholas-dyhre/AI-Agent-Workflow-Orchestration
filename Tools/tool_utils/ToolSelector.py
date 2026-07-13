from Agent.BaseAgent import BaseAgent
from Tools.Tool import Tool
from Tools.tool_utils.ToolRegistry import ToolRegistry


class ToolSelector:
    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    def select(self, agent: BaseAgent):

        tools = {}

        for tool in self.registry.list().values():

            if self.is_allowed(agent, tool):
                tools[tool.name] = tool

        return tools
            
    def is_allowed(
        self,
        agent: BaseAgent,
        tool: Tool
    ):

        # Explicit deny wins
        if any(
            capability in agent.denied_capabilities
            for capability in tool.capabilities
        ):
            return False


        # Capability match
        capability_match = any(
            capability in agent.allowed_capabilities
            for capability in tool.capabilities
        )


        # Tag match
        tag_match = any(
            tag in agent.allowed_tags
            for tag in tool.tags
        )


        return capability_match or tag_match
    
# from typing import Dict, List
# from Agent.AgentNames import AgentName
     # def _get_tool_names(self, agent_name: AgentName) -> List[str]:
    #     match agent_name:
    #         case AgentName.DEVELOPER:
    #             return [
    #                 "code_generator",
    #                 "file_reader",
    #                 "code_runner",
    #                 "git_tool",
    #             ]

    #         case AgentName.REVIEWER:
    #             return [
    #                 "file_reader",
    #                 "diff_reader",
    #             ]

    #         case _:
    #             return []

     # def select(self, agent_name: AgentName) -> Dict[str, Tool]:
    #     tool_names = self._get_tool_names(agent_name)

    #     # Validate registry contains them
    #     self.registry.require(tool_names)

    #     # Build dictionary
    #     return {
    #         name: self.registry.get(name)
    #         for name in tool_names
    #     }
    
    # def select_by_tags(self, tags: List[str]) -> Dict[str, Tool]:
    #     tools = self.registry.find_by_tags(tags)

    #     return {tool.name: tool for tool in tools}