from Skills.skill_utils.SkillNode import SkillNode
from Skills.skill_utils.SkillSelector import SkillSelector
from Tasks.Task import Task
from Tools.tool_utils.ToolCapability import ToolCapability
from Tools.tool_utils.ToolTag import ToolTag


class AgentSkillRepository:
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
    def __init__(self, skill_selector: SkillSelector):
        self.skill_selector = skill_selector
        self.skill_name_added: set[str] = set()
        self.skill_keywords_added: set[str] = set()
        self.skills: list[SkillNode] = []
        self.skill_count_limit = 6
        # self.tools: Dict[str, Tool] = skill_selector.select(prompt)

    def prepare(self, work_item: str | Task):
        self.skills = self.skill_selector.select(work_item)
        self.add_skills(self.skills)

    def can_load_skills(self) -> bool:
        return (len(self.skills) < self.skill_count_limit)

    def update_skills_used(self):
        for skill in self.skills:
            self.skill_name_added.add(skill.name)

    def add_skills(self, skillNodes: list[SkillNode] | None, skill_keywords: list[str] | None = None) -> None:
        if skillNodes:
            for skill_node in skillNodes:
                self.add_skill(skill_node)
        if skill_keywords:
            for skill_tag in skill_keywords:
                self.add_skill(None, skill_tag)

    def add_skill(self, skillNode: SkillNode | None, skill_keyword: str | None = None) -> None:
        if skillNode and skillNode.name:
            if skillNode.name not in self.skill_name_added:
                self.skills.append(skillNode)
                self.skill_name_added.add(skillNode.name)
                print(f"Adding {skillNode.name} to the skill list.")
            else: 
                print(f"Skill {skillNode.name} already added.")
        elif skill_keyword and isinstance(skill_keyword, str):
            if skill_keyword not in self.skill_keywords_added:
                self.skill_keywords_added.add(skill_keyword)
        else:
            print(f"Skill node or skill tag is None. \n")

    def get_allowed_skill_nodes(self):
        return [
            node for node in self.skill_selector.list_skills()
            if node.name not in self.skill_name_added
            and not any(keyword in self.skill_keywords_added for keyword in node.keywords)
        ]

    