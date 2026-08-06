from typing import Type
from pydantic import BaseModel
from Tools.Tool import Tool, ToolOutput
from Tools.Git.GitUtils import GitUtils
from Tools.tool_utils.ToolTag import ToolTag
from Tools.tool_utils.ToolCapability import ToolCapability

class GitCreateRepositoryInput(BaseModel):
    pass

class GitCreateRepositoryOutput(ToolOutput):
    execution_log: str

class GitCreateRepositoryTool(Tool[GitCreateRepositoryInput, GitCreateRepositoryOutput]):
    name: str = "GitCreateRepositoryTool"
    description: str = "Initializes an entirely clean Git tracking instance environment inside the project directory root."
    tags: list[ToolTag] = [ToolTag.GIT, ToolTag.DEVELOPMENT]
    capabilities: list[ToolCapability] = [ToolCapability.EXECUTE_COMMANDS, ToolCapability.CREATE_REPOSITORY, ToolCapability.GIT]
    path: str = "Tools/GitCreateRepositoryTool.py"
    input_model: Type[GitCreateRepositoryInput] = GitCreateRepositoryInput
    output_model: Type[GitCreateRepositoryOutput] = GitCreateRepositoryOutput

    def run(self, input: GitCreateRepositoryInput) -> GitCreateRepositoryOutput:
        try:
            res_msg = GitUtils.create_repository()
            return GitCreateRepositoryOutput(execution_log=res_msg, success="Success" in res_msg or "Notice" in res_msg, message=res_msg)
        except Exception as e:
            return GitCreateRepositoryOutput(execution_log="", success=False, message=f"Repository creation crashed: {str(e)}")