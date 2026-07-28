import re
from pathlib import Path
from Skills.skill_utils.SkillNode import SkillNode


class SkillTreeBuilder:
    def __init__(self, root_file: str):
        self.root_file = Path(root_file)
        self.root_folder = self.root_file.parent
        self.node_registry: dict[str, SkillNode] = {}

    def build(self) -> SkillNode:
        self._discover_all_nodes()
        root_name = self.root_file.stem
        root = self.node_registry.get(root_name)
        if not root:
            root = SkillNode(
                name=root_name,
                keywords=["Root"],
                path=self.root_file.resolve()
            )
            self.node_registry[root_name] = root
        else:
            root.keywords = ["Root"]
        self._assemble_tree(root, visited=set())

        print(f"skill tree root path: {self.root_file.resolve()}")
        return root

    def _discover_all_nodes(self):
        """Recursively scans the root directory to index all SkillNodes by their name."""
        for file_path in self.root_folder.rglob("*.md"):
            node = SkillNode(
                name=file_path.stem,
                keywords=[],  # Will be populated in the assembly step
                path=file_path.resolve()
            )
            self.node_registry[file_path.stem] = node

    def _assemble_tree(self, parent_node: SkillNode, visited: set[Path]):
        """Reads a file to assign keywords to children and hook up parent-child links."""

        if not parent_node.path:
            print(f"[WARN] Missing file: {parent_node.name}")
            return

        if parent_node.path in visited:
            return
        
        visited.add(parent_node.path)

        content = parent_node.load()

        pattern = r"^\s*-\s*([^→\-\n]+?)\s*(?:→|->)\s*([^\r\n]+)$"
        for keywords_raw, name_raw in re.findall(pattern, content, re.MULTILINE):
            child_name = name_raw.strip().strip("`").strip()
            keywords = [k.strip() for k in keywords_raw.split(",") if k.strip()]
            child_node = self.node_registry.get(child_name)
            
            if child_node:
                child_node.keywords = keywords
                
                parent_node.children.append(child_node)
                
                if child_node.path:
                    self._assemble_tree(child_node, visited)
            else:
                print(f"[WARN] Found reference to skill '{child_name}', but no file named '{child_name}.md' exists.")

    def build_and_format(self) -> str:
        tree = self.build()
        return self.format_tree_to_prompt(tree)

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
