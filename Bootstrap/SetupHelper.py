from pathlib import Path
from Skills.skill_utils.SkillRegistry import SkillRegistry
from Skills.skill_utils.SkillSelector import SkillSelector
from Skills.skill_utils.SkillTreeBuilder import SkillTreeBuilder
from Tools.models.ToolContextKey import ToolContextKey
from Tools.tool_utils.ToolRegistry import ToolRegistry
from Tools.tool_utils.ToolSelector import ToolSelector
from Tools.tool_utils.ToolDiscovery import ToolDiscovery


class SetupHelper:
    @staticmethod
    def CreateToolRegistry(skillRegistry: SkillRegistry, task_base_path: str) -> ToolSelector:
        if not skillRegistry:
            raise Exception("Tool registry requires skill registry to be provided.")
        registry = ToolRegistry()
        current_dir = Path(__file__).resolve().parent
        project_root = current_dir.parent
        tools_path = project_root / "Tools"

        tools = ToolDiscovery.discover_tools(Path(tools_path))

        context = {
            ToolContextKey.skill_registry: skillRegistry,
            ToolContextKey.task_base_path: task_base_path
        }
        for tool in tools:
            tool.initialize(context)
            registry.register(tool)

        return ToolSelector(registry)

    @staticmethod
    def create_skill_selector(skillRegistry: SkillRegistry) -> SkillSelector:
        if not skillRegistry:
            raise Exception("Skill selector requires skill registry to be provided.")

        return SkillSelector(skillRegistry)

    @staticmethod
    def create_skill_registry(root_skill_file: str = "./Skills/RootSkillNode.md") -> SkillRegistry:
        builder = SkillTreeBuilder(root_skill_file)
        rootNode = builder.build()
        return SkillRegistry(rootNode)
