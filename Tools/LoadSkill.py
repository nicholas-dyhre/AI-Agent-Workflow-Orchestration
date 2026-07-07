
from pydantic import BaseModel

from Skills.skill_utils.SkillNode import SkillNode
from Tools.Tool import Tool


class LoadSkillInput(BaseModel):
    skill_path: str

class LoadSkillTool(Tool):
    name = "load_skill"
    description = "Load a specific skill into context"
    input_model = LoadSkillInput

    def __init__(self, skill_tree: SkillNode):
        self.skill_tree = skill_tree

    def run(self, input: LoadSkillInput):
        node = self._find_node(self.skill_tree, input.skill_path.split("/"))

        if not node or not node.path:
            raise ValueError(f"Skill not found: {input.skill_path}")

        with open(node.path) as f:
            content = f.read()

        return {"Loaded Skill": f"loaded skill {input.skill_path}\n\n{content}"}
    
    def _find_node(self, current: SkillNode, path_parts: list[str]) -> SkillNode | None:
        if not path_parts:
            return current

        next_name = path_parts[0]

        for child in current.children:
            if child.name == next_name:
                return self._find_node(child, path_parts[1:])

        return None