from pathlib import Path
from typing import List

from Skills.skill_utils.SkillNode import SkillNode
from Skills.skill_utils.SkillRegistry import SkillRegistry
from Tasks.Task import Task


class SkillSelector:
    def __init__(self, registry: SkillRegistry):
        self.registry = registry

    def select(self, task: Task | str) -> List[SkillNode]:
        if isinstance(task, Task):
            return self._select_task(task)

        elif isinstance(task, str):
            return self._select_string(task)

        raise TypeError(f"Unsupported type: {type(task)}")
    
    def list_skills(self) -> List[SkillNode]:
        return self.registry.list()

    def get_root(self) -> SkillNode:
        return self.registry.tree()

    def _select_task(self, task: Task) -> List[SkillNode]:
        text = f"{task.title} {task.description}"
        return self._select_text(text)


    def _select_string(self, prompt: str) -> List[SkillNode]:
        return self._select_text(prompt)


    def _select_text(self, text: str) -> List[SkillNode]:
        words = text.lower().split()
        return self.registry.find_matching_nodes(words)