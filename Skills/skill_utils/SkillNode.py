from dataclasses import dataclass, field
from typing import List, Optional


# @dataclass
# class SkillNode:
#     name: str
#     path: Optional[str] = None
#     children: List["SkillNode"] = []

#     def __post_init__(self):
#         self.children = self.children or []
@dataclass
class SkillNode:
    name: str
    keywords: List[str] = field(default_factory=list)
    path: Optional[str] = None
    children: List["SkillNode"] = field(default_factory=list)

    def get_descendants(self):
        result = []
        for child in self.children:
            result.append(child)
            result.extend(
                child.get_descendants()
            )

        return result
    
    def node_to_prompt(self, depth: int = 0) -> str:
        lines = [f"[{self.name}]"]
        indent = "  " * depth

        if self.keywords:
            lines.append(f"{indent}- keywords: {', '.join(self.keywords)}")

        if self.path:
            lines.append(f"{indent}- file: {self.path}")

        lines.append("")
        return "\n".join(lines)
    
    def branch_to_prompt(self, depth: int = 0) -> str:
        def recurse(node, indent=depth):
            s = "  " * indent + f"- {node.name}\n"
            for child in node.children:
                s += recurse(child, indent + 1)
            return s

        return recurse(self)