from Skills.skill_utils.SkillRegistry import SkillRegistry

class SkillSelector:
    def __init__(self, registry: SkillRegistry):
        self.registry = registry
    
    def select(self, task):
        words = (
            f"{task.title} {task.description}"
            .lower()
            .split()
        )

        nodes = self.registry.find_matching_nodes(
            words
        )

        return nodes