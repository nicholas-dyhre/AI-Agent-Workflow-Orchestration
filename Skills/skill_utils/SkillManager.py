from Skills.skill_utils.SkillNode import SkillNode
from Skills.skill_utils.SkillRegistry import SkillRegistry
from Skills.skill_utils.SkillTreeBuilder import SkillTreeBuilder


class SkillManager:

    def __init__(self, root_skill_file: str):
        self.root_skill_file = root_skill_file
        self.registry = SkillRegistry(self._getSkillTree())

    def _getSkillTree(self) -> SkillNode:

        builder = SkillTreeBuilder(
            self.root_skill_file
        )

        rootNode = builder.build()
        return rootNode

    def get_registry(self):
        return self.registry