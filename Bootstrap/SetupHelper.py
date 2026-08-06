from pathlib import Path
from Skills.skill_utils.SkillRegistry import SkillRegistry
from Skills.skill_utils.SkillSelector import SkillSelector
from Skills.skill_utils.SkillTreeBuilder import SkillTreeBuilder
from Tools.Git.GitUtils import GitUtils
from Tools.code.CodeUtils import CodeUtils
from Tools.models.ToolContextKey import ToolContextKey
from Tools.tool_utils.ToolRegistry import ToolRegistry
from Tools.tool_utils.ToolSelector import ToolSelector
from Tools.tool_utils.ToolDiscovery import ToolDiscovery
from Tools.Task.TaskFileUtils import TaskFileUtils


class SetupHelper:
    @staticmethod
    def CreateToolRegistry(skillRegistry: SkillRegistry, repo_path: str, task_base_path: str) -> ToolSelector:
        if not skillRegistry:
            raise Exception("Tool registry requires skill registry to be provided.")
        registry = ToolRegistry()
        current_dir = Path(__file__).resolve().parent
        project_root = current_dir.parent
        tools_path = project_root / "Tools"

        tools = ToolDiscovery.discover_tools(Path(tools_path))

        context = {
            ToolContextKey.skill_registry: skillRegistry,
            ToolContextKey.task_base_path: task_base_path,
            ToolContextKey.repo_path: repo_path
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

    @staticmethod
    def setup_utils_with_paths(repo_path: str, task_base_path: str) -> None:
        TaskFileUtils.set_task_path(task_base_path)
        GitUtils.set_repo_path(repo_path)
        CodeUtils.set_base_path(repo_path)
