from pathlib import Path
from typing import List, Optional
from typing import Generator
from Skills.skill_utils.SkillNode import SkillNode
from Common.ListUtils import flatten


class SkillRegistry:
    def __init__(self, rootNode: SkillNode):
        self._root = rootNode
        self._index = self._build_index()

    def _build_index(self) -> dict[str, SkillNode]:
        """
        Creates a fast lookup table by skill name.

        The tree remains the source of truth.
        This is only an optimization.
        """

        index = {}

        for node in self.walk():
            if node.name != "root":
                index[node.name] = node

        return index

    def get(self, name: str) -> Optional[SkillNode]:
        """Get a skill by exact name."""
        return self._index.get(name)

    def require(self, name: str) -> SkillNode:
        """
        Get a skill or fail loudly.
        Useful when a skill is mandatory.
        """

        skill = self.get(name)

        if skill is None:
            raise ValueError(f"Skill not found: {name}")

        return skill

    def has(self, name: str) -> bool:
        return name in self._index

    def list(self) -> List[SkillNode]:
        return list(self._index.values())

    def list_unique_keywords(self) -> set[str]:
        keywords: set[str] = flatten([node.keywords for node in self._index.values()])
        return keywords

    def list_unique_names(self) -> set[str]:
        names: set[str] = set([node.name for node in self._index.values()])
        return names

    def search(self, keyword: str) -> List[SkillNode]:
        """Find skills matching a keyword."""

        keyword = keyword.lower()

        return [
            skill
            for skill in self._index.values()
            if any(keyword in k.lower() for k in skill.keywords)
        ]

    def find_by_keywords(self, keywords: List[str]) -> List[SkillNode]:
        """Find skills matching multiple keywords."""

        keywords = [k.lower() for k in keywords]

        results = []

        for skill in self._index.values():
            skill_keywords = [k.lower() for k in skill.keywords]

            if any(k in skill_keywords for k in keywords):
                results.append(skill)

        return results

    def children_of(self, skill_name: str) -> List[SkillNode]:
        """Get immediate children of a skill."""

        skill = self.require(skill_name)

        return skill.children

    def branch(self, skill_name: str) -> List[SkillNode]:
        """Get a complete skill subtree."""
        skill = self.require(skill_name)
        return list(skill.get_descendants())

    def tree(self) -> SkillNode:
        return self._root

    def find_matching_nodes(self, keywords: List[str]) -> List[SkillNode]:
        matches = []

        self._search(self._root, keywords, matches)

        return matches

    def _search(self, node, keywords, matches):
        if any(keyword.lower() in [k.lower() for k in node.keywords] for keyword in keywords):
            matches.append(node)

        for child in node.children:
            self._search(child, keywords, matches)

    def walk(self) -> Generator[SkillNode, None, None]:
        """
        Depth-first traversal of the skill tree. Yields every SkillNode starting from root.
        """

        yield from self._walk_node(self._root)

    def _walk_node(self, node: SkillNode) -> Generator[SkillNode, None, None]:

        yield node

        for child in node.children:
            yield from self._walk_node(child)
