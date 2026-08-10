from typing import Dict, List
from Tools.Tool import Tool
from Tools.tool_utils.ToolCapability import ToolCapability
from Tools.tool_utils.ToolSelector import ToolSelector
from Tools.tool_utils.ToolTag import ToolTag


class AgentToolRepository:

    DEFAULT_ALLOWED_TAGS = [
        ToolTag.TASKS, 
        ToolTag.UTILITY, 
        ToolTag.SKILLS
    ]
    DEFAULT_ALLOWED_CAPABILITIES = [
        ToolCapability.UPDATE_TASKS, 
        ToolCapability.LOAD_SKILL
    ]
    DEFAULT_DENIED_CAPABILITIES = [
        ToolCapability.RESTRCITED_UNTIL_FURTHER_CLARIFICATION, 
        ToolCapability.CREATE_REPOSITORY, 
        ToolCapability.CREATE_BRANCH,
    ]
    def __init__(self, tool_selector: ToolSelector):
        self.tool_selector = tool_selector
        self.allowed_tags = self.DEFAULT_ALLOWED_TAGS.copy()
        self.allowed_capabilities = self.DEFAULT_ALLOWED_CAPABILITIES.copy()
        self.denied_capabilities = self.DEFAULT_DENIED_CAPABILITIES.copy()
        self.tools: Dict[str, Tool] = {}

    def get_tool(self, tool_name: str) -> Tool | None:
        return self.tools.get(tool_name)

    def prepare(self) -> None:
        self.tools = self.tool_selector.select(self)

    def disable_tools(self, toolCapabilities: list[ToolCapability] | None, tooltags: list[ToolTag] | None) -> None:
        if toolCapabilities:
            self.disable_tool_by_capabilities(toolCapabilities)

        if tooltags:
            self.dissable_tool_by_tags(tooltags)

    def disable_tool_by_capabilities(self, toolCapabilities: List[ToolCapability]) -> None:
        for capability in toolCapabilities:
            if capability not in self.denied_capabilities:
                self.denied_capabilities.append(capability)
                print(f"Disabling capability: {capability}")
            else:
                print(f"Capability {capability} already disabled.")

    def dissable_tool_by_tags(self, tooltags: list[ToolTag]) -> None:
        for tag in tooltags:
            if tag in self.allowed_tags:
                self.allowed_tags = [t for t in self.allowed_tags if t != tag]
                print(f"Disabling tag: {tag}")
            else:
                print(f"Tag {tag} already disabled or not present.")

    def __disable_tools(self, toolCapabilities: list[ToolCapability] | None, tooltags: list[ToolTag] | None) -> None:
        if toolCapabilities:
            for capability in toolCapabilities:
                if capability not in self.denied_capabilities:
                    self.denied_capabilities.append(capability)
                    print(f"Disabling capability: {capability}")
                else:
                    print(f"Capability {capability} already disabled.")

                if capability in self.allowed_capabilities:
                    self.allowed_capabilities = [c for c in self.allowed_capabilities if c != capability]
                    print(f"Removing all instances of capability from allowed: {capability}")
                    
        if tooltags:
            for tag in tooltags:
                if tag in self.allowed_tags:
                    self.allowed_tags = [t for t in self.allowed_tags if t != tag]
                    print(f"Disabling tag: {tag}")
                else:
                    print(f"Tag {tag} already disabled or not present.")

        self.tools = self.tool_selector.select(self)