import os
import re
from pathlib import Path
import sys

from SkillNode import SkillNode

class SkillTreeBuilder:
    def __init__(self, root_folder: str):
        self.root = Path(root_folder)


    def build(self) -> SkillNode:
        root = SkillNode(name="root")
        self._parse_file(self.root / "RootSkillNode.md", root)
        print(self.root) # Debug step
        return root

    def _parse_file(self, file_path: Path, parent: SkillNode):
        if not file_path.exists():
            return

        fileName = file_path.stem
        content = file_path.read_text(encoding="utf-8")

        pattern = r"-\s*(.+?)\s*→\s*(.+)"

        for keywords_raw, path_raw in re.findall(pattern, content):
            keywords = [k.strip() for k in keywords_raw.split(",")]
            path = path_raw.strip()

            node = SkillNode(
                name=fileName,
                keywords=keywords,
                path=str(self.root / path.lstrip("./"))
            )

            parent.children.append(node)

            # recurse into subskills
            if node.path is not None:
                self._parse_file(Path(node.path), node)

    def format_tree_to_prompt(self, root: SkillNode) -> str:
        lines = ["SKILL TREE\n"]
        self._format_node(root, lines, depth=0)
        return "\n".join(lines)


    def _format_node(self, node: SkillNode, lines: list, depth: int):
        indent = "  " * depth

        # Skip root label noise
        if node.name != "root":
            lines.append(f"{indent}[{node.name}]")

            if node.keywords:
                lines.append(f"{indent}- keywords: {', '.join(node.keywords)}")

            if node.path:
                lines.append(f"{indent}- file: {node.path}")

            lines.append("")  # spacing

        for child in node.children:
            self._format_node(child, lines, depth + 1)
        
# =========================
# CLI ENTRY POINT
# =========================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python skillTreeBuilder.py <path_to_root_file.md>")
        sys.exit(1)

    root_file = sys.argv[1]

    builder = SkillTreeBuilder(root_file)
    tree = builder.build()

    output = builder.format_tree_to_prompt(tree)

    print("\n===== SKILL TREE OUTPUT =====\n")
    print(output)