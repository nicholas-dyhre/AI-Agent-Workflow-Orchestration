from typing import Any, List, Optional, Type
from pydantic import BaseModel, Field, PrivateAttr
from Skills.skill_utils.SkillNode import SkillNode
from Skills.skill_utils.SkillRegistry import SkillRegistry
from Tools.Tool import Tool, ToolOutput
from Tools.models.ToolContextKey import ToolContextKey
from Tools.tool_utils.ToolTag import ToolTag
from Tools.tool_utils.ToolCapability import ToolCapability

class LoadSkillInput(BaseModel):
    skill_names: list[str] = Field(
        ...,
        description="The path to the skill file to be loaded into",
    )
    skill_keywords: list[str] = Field(
        ...,
        description="The keywords to search for in the skill file",
    )

class LoadSkillOutput(ToolOutput):
    skill_nodes: list[SkillNode] | None = None
    skill_keywords: list[str] | None = None

    def to_string(self) -> str:
        result = super().to_string()

        if self.skill_nodes:
            for node in self.skill_nodes:
                result += f"- {node.name} \n"

        return result
    
class LoadSkillTool(Tool[LoadSkillInput, LoadSkillOutput]):
    name: str = "LoadSkillTool"
    description: str = "Injects functional contextual operational code instructions directly into the active Agent system workspace."
    tags: List[ToolTag] = [ToolTag.SKILLS, ToolTag.UTILITY]
    capabilities: List[ToolCapability] = [ToolCapability.LOAD_SKILL]
    path: str = "Tools/LoadSkillTool.py"
    input_model: Type[BaseModel] = LoadSkillInput
    output_model: Type[LoadSkillOutput] = LoadSkillOutput

    _skill_registry: Optional[SkillRegistry] = PrivateAttr()
    
    def initialize(self, context: dict[ToolContextKey, Any]) -> None:
        skill_registry = context[ToolContextKey.skill_registry]
        if skill_registry is None:
            raise Exception("No skill registry provided in context")
        if not isinstance(skill_registry, SkillRegistry):
            raise TypeError("skill_registry must be a SkillRegistry")
        if not all(isinstance(node, SkillNode) for node in skill_registry.list()):
            raise TypeError("All items in skill_tree must be SkillNode")

        self._skill_registry = skill_registry

    def run(self, input: LoadSkillInput) -> LoadSkillOutput:
        if not self._skill_registry: 
            raise ValueError("skillRegistry has not been configured via initialize().") 
        
        nodes = self._find_nodes(input) 
        if not nodes:
            return LoadSkillOutput(
                skill_nodes = None,
                skill_keywords = None,
                success = False,
                message = f"You have tried to provided invalid names or keywords. Please use the skill names or keywords provided in AVAILABLE SKILLS \n"
            )

        return LoadSkillOutput(
            skill_nodes = nodes,
            skill_keywords = input.skill_keywords,
            success = True,
            message = f"Successfully loaded skills {len(nodes)} skills \n",
        )

    def _find_nodes(self, input: LoadSkillInput) -> list[SkillNode] | None:
        raw_nodes = self._find_by_names(input.skill_names)
        raw_keyword_nodes = self._find_by_keywords(input.skill_keywords)

        nodes: list[SkillNode] = raw_nodes if raw_nodes is not None else []
        keyword_nodes: list[SkillNode] = raw_keyword_nodes if raw_keyword_nodes is not None else []

        combined = nodes + keyword_nodes
        
        seen = set()
        merged = []
        for node in combined:
            if node and node.name and node.name not in seen:
                seen.add(node.name)
                merged.append(node)
        print(f"found {len(merged)} skill nodes")
        return merged if merged else None

    def _find_by_names(self, skill_names: list[str]) -> list[SkillNode] | None:
        nodes: list[SkillNode] = []
        for skill_name in skill_names:
            node = self._find_by_name(skill_name)
            if node is not None:
                nodes.append(node)
        return nodes
    
    def _find_by_name(self, skill_name: str) -> SkillNode | None:
        if self._skill_registry is None:
            raise ValueError("skillRegistry has not been configured via initialize().")
        node_result = self._skill_registry.get(skill_name)
        if node_result is not None:
            return node_result
        print("Could not find skill path: ", skill_name)

    def _find_by_keywords(self, skill_keywords: list[str]) -> list[SkillNode] | None:
        if self._skill_registry is None:
            raise ValueError("skillRegistry has not been configured via initialize().")
        nodes = self._skill_registry.find_by_keywords(skill_keywords)
        return nodes




