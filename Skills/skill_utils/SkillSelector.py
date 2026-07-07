from typing import List

from Agent.AgentNames import AgentName
from Skills.skill_utils.Skill import Skill
from Skills.skill_utils.SkillRegistry import SkillRegistry
from Tasks.Task import Task


class SkillSelector:
    def __init__(self, registry: SkillRegistry):
        self.registry = registry

    def select(self, task: Task) -> List[Skill]:
        selected = []

        text = f"{task.title} {task.description}".lower()

        if "angular" in text:
            selected.append(self.registry.get("angular_root"))

            if "rxjs" in text or "async" in text:
                selected.append(self.registry.get("angular_async"))

            if "performance" in text:
                selected.append(self.registry.get("angular_performance"))

            if "state" in text:
                selected.append(self.registry.get("angular_state"))

        return selected