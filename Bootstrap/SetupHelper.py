from Skills.skill_utils.SkillManager import SkillManager
from Skills.skill_utils.SkillRegistry import SkillRegistry
from Skills.skill_utils.SkillSelector import SkillSelector
from Skills.skill_utils.SkillTreeBuilder import SkillTreeBuilder
from Tools.tool_utils.ToolRegistry import ToolRegistry
from Tools.tool_utils.ToolSelector import ToolSelector
from Tools.tool_utils.ToolDiscovery import ToolDiscovery


class SetupHelper:

    @staticmethod
    def CreateToolRegistry() -> ToolSelector:

        registry = ToolRegistry()

        tool_classes = ToolDiscovery.discover_tools(
            "Tools"
        )

        for tool_class in tool_classes:
            registry.register(
                tool_class(...)
            )

        return ToolSelector(registry)
    
    @staticmethod
    def create_skill_selector() -> SkillSelector:
        registry = SetupHelper.create_skill_registry("./Skills/RootSkillNode.md")
        return SkillSelector(registry)
    
    @staticmethod
    def create_skill_registry(root_skill_file: str = "./Skills/RootSkillNode.md") -> SkillRegistry:
        builder = SkillTreeBuilder(root_skill_file)
        rootNode = builder.build()
        return SkillRegistry(rootNode)