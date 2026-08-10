from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Dict, Union, Any, overload

if TYPE_CHECKING:
    from Agent.BaseAgent import BaseAgent
    from Agent.AgentToolRepository import AgentToolRepository
    from Tools.Tool import Tool
    from Tools.tool_utils.ToolCapability import ToolCapability
    from Tools.tool_utils.ToolRegistry import ToolRegistry
    from Tools.tool_utils.ToolTag import ToolTag

# Placeholder type definitions to ensure the code compiles
# class ToolCapability: pass
# class ToolTag: pass
# class Tool:
#     name: str
#     capabilities: List[ToolCapability]
#     tags: List[ToolTag]
# class ToolRegistry:
#     def list(self) -> Dict[str, Tool]: return {}
# class BaseAgent: pass
# class AgentToolRepository: pass

@dataclass
class AllowedInput:
    denied_capabilities: List[ToolCapability]
    allowed_capabilities: List[ToolCapability]
    allowed_tags: List[ToolTag]

class ToolSelector:
    def __init__(self, registry: ToolRegistry):
        self.registry = registry
        
    @overload
    def select(self, target: BaseAgent) -> Dict[str, Tool]: ...
    
    @overload
    def select(self, target: AgentToolRepository) -> Dict[str, Tool]: ...

    def select(self, target: Union[BaseAgent, AgentToolRepository]) -> Dict[str, Tool]:
        """Selects allowed tools based on the agent or repository properties."""
        tools = {}
        # Extract the allowed/denied properties dynamically from the object
        allowed_input = self.__try_get_properties_from_type(target)

        for tool in self.registry.list().values():
            if self.__is_allowed(allowed_input, tool):
                tools[tool.name] = tool

        return tools

    def __try_get_properties_from_type(self, model: Any) -> AllowedInput:
        """Extracts tool constraints from a given model object."""
        try:
            denied_capabilities = getattr(model, 'denied_capabilities', [])
            allowed_capabilities = getattr(model, 'allowed_capabilities', [])
            allowed_tags = getattr(model, 'allowed_tags', [])
            return AllowedInput(denied_capabilities, allowed_capabilities, allowed_tags)
        except AttributeError:
            raise AttributeError("Model does not have denied capabilities, allowed capabilities, or allowed tags")
        except Exception as e:
            raise Exception(f"Could not extract type. Error: {e}")

    def __is_allowed(self, allowed_input: AllowedInput, tool: Tool) -> bool:
        """Evaluates if a tool is allowed based on the filtered constraints."""
        # Explicit deny wins
        if any(capability in allowed_input.denied_capabilities for capability in tool.capabilities):
            return False

        # Capability match
        capability_match = any(
            capability in allowed_input.allowed_capabilities for capability in tool.capabilities
        )

        # Tag match
        tag_match = any(tag in allowed_input.allowed_tags for tag in tool.tags)
        return capability_match or tag_match


# @dataclass
# class AllowedInput:
#     denied_capabilities: List[ToolCapability]
#     allowed_capabilities: List[ToolCapability]
#     allowed_tags: List[ToolTag]

# class ToolSelector:
#     def __init__(self, registry: ToolRegistry):
#         self.registry = registry
        
#     @overload
#     def select(self, agent: BaseAgent) -> Dict[str, Tool]:

#         tools = {}

#         for tool in self.registry.list().values():
#             if self.is_allowed(agent, tool):
#                 tools[tool.name] = tool

#         return tools
#     @overload
#     def select(self, agentToolRepository: AgentToolRepository) -> Dict[str, Tool]:
#         tools = {}
        
#         for tool in self.registry.list().values():
#             if self.is_allowed(agent, tool):
#                 tools[tool.name] = tool

#         return tools

    

#     def try_get_properties_from_type(self, model: class) -> allowed_input:
#         try:
#             denied_capabilities = model.denied_capabilities
#             allowed_capabilities = model.allowed_capabilities
#             allowed_tags = model.allowed_tags
#             return AllowedInput(denied_capabilities, allowed_capabilities, allowed_tags)
#         except AttributeError:
#             raise AttributeError("Model does not have denied capabilities, allowed capabilities or allowed tags")
#         except Exception as e:
#             raise Exception(f"Could not extract type. Error: {e}")

#     def is_allowed(self, AllowedInput: AllowedInput, tool: Tool):
    
#             # Explicit deny wins
#             if any(capability in AllowedInput.denied_capabilities for capability in tool.capabilities):
#                 return False
    
#             # Capability match
#             capability_match = any(
#                 capability in AllowedInput.allowed_capabilities for capability in tool.capabilities
#             )
    
#             # Tag match
#             tag_match = any(tag in AllowedInput.allowed_tags for tag in tool.tags)
#             return capability_match or tag_match

#     def is_allowed(self, agent: BaseAgent, tool: Tool):

#         # Explicit deny wins
#         if any(capability in agent.denied_capabilities for capability in tool.capabilities):
#             return False

#         # Capability match
#         capability_match = any(
#             capability in agent.allowed_capabilities for capability in tool.capabilities
#         )

#         # Tag match
#         tag_match = any(tag in agent.allowed_tags for tag in tool.tags)
#         return capability_match or tag_match