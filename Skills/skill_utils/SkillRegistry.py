from typing import Dict

from Skills.skill_utils.Skill import Skill


class SkillRegistry:
    def __init__(self):
        self.skills: Dict[str, Skill] = {}

    def register(self, skill: Skill):
        self.skills[skill.name] = skill

    def get(self, name: str) -> Skill:
        return self.skills[name]