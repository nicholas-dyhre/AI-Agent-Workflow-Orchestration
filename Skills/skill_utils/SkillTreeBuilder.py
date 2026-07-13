import re
from pathlib import Path
from SkillNode import SkillNode


class SkillTreeBuilder:
    def __init__(self, root_file: str):
        self.root_file = Path(root_file).resolve()
        self.root_folder = self.root_file.parent
        self.visited = set()

    def build(self) -> SkillNode:
        root = SkillNode(name="root")
        self._parse_file(self.root_file, root)
        print(self.root_file)
        return root

    def _parse_file(self, file_path: Path, parent: SkillNode):
        file_path = file_path.resolve()

        if file_path in self.visited:
            return
        self.visited.add(file_path)

        if not file_path.exists():
            print(f"[WARN] Missing file: {file_path}")
            return

        content = file_path.read_text(encoding="utf-8")

        pattern = r"^\s*-\s*([^\n→]+?)\s*→\s*([^\n]+)$"

        for keywords_raw, path_raw in re.findall(pattern, content, re.MULTILINE):
            keywords = [k.strip() for k in keywords_raw.split(",") if k.strip()]

            resolved_path = (self.root_folder / path_raw.lstrip("./")).resolve()

            node = SkillNode(
                name=resolved_path.stem,
                keywords=keywords,
                path=str(resolved_path)
            )

            parent.children.append(node)

            if resolved_path.suffix == ".md":
                self._parse_file(resolved_path, node)

    def format_tree_to_prompt(self, root: SkillNode) -> str:
        lines = ["SKILL TREE\n"]
        self._format_node(root, lines, depth=0)
        return "\n".join(lines)

    def _format_node(self, node: SkillNode, lines: list, depth: int):
        indent = "  " * depth

        if node.name != "root":
            lines.append(f"{indent}[{node.name}]")

            if node.keywords:
                lines.append(f"{indent}- keywords: {', '.join(node.keywords)}")

            if node.path:
                lines.append(f"{indent}- file: {node.path}")

            lines.append("")

        for child in node.children:
            self._format_node(child, lines, depth + 1)


    def build_and_format(self) -> str:
        tree = self.build()
        return self.format_tree_to_prompt(tree)