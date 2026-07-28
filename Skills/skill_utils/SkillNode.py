from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import List, Optional

@dataclass
class SkillNode:
    name: str
    keywords: List[str] = field(default_factory=list)
    path: Optional[Path] = None
    children: List["SkillNode"] = field(default_factory=list)

    def get_descendants(self):
        result = []
        for child in self.children:
            result.append(child)
            result.extend(child.get_descendants())

        return result

    def node_to_prompt(self, depth: int = 0) -> str:
        indent = "  " * depth
        lines = [f"{indent}[{self.name}]"]

        if self.keywords:
            lines.append(f"{indent}- keywords: {', '.join(self.keywords)}")

        if self.path:
            lines.append(f"{indent}- file: {self.path}")

        lines.append("\n")
        return "\n".join(lines)

    def branch_to_prompt(self, depth: int = 0) -> str:
        def recurse(node, indent=depth):
            s = node.node_to_prompt(depth=indent)
            for child in node.children:
                s += recurse(child, indent + 1)
            return s

        return recurse(self)

    def load(self, toPrune: bool = False) -> str:
        if self.path:
            with open(self.path, encoding="utf-8") as f:
                if(toPrune):
                    return self.__prune_skill_section(f.read())
                return f.read()
        else:
            raise FileNotFoundError(f"File not found: {self.path}")

    def __prune_skill_section(self, content: str) -> str:
        target_pattern = re.compile(r"^\s*-\s*([^→\-\n]+?)\s*(?:→|->)\s*([^\r\n]+)$", re.MULTILINE)
        sections = re.split(r"(\n^---\s*$\n|\n^---\s*$|^---\s*$\n)", content, flags=re.MULTILINE)
        
        pruned_sections = []
        skip_next_divider = False

        for i, section in enumerate(sections):
            if re.match(r"^---\s*$", section.strip()):
                if skip_next_divider:
                    skip_next_divider = False
                    continue
                pruned_sections.append(section)
                continue
            if target_pattern.search(section):
                if pruned_sections and re.match(r"^---\s*$", pruned_sections[-1].strip()):
                    pruned_sections.pop()
                else:
                    skip_next_divider = True
                continue

            pruned_sections.append(section)
        return "".join(pruned_sections)
