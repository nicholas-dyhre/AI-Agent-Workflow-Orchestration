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