from Tools.CodeGeneratorTool import CodeGeneratorTool
from Tools.CodeRunnerTool import CodeRunnerTool
from Tools.CreateBranchTool import CreateBranchTool
from Tools.CreatePRTool import CreatePRTool
from Tools.DiffTool import DiffTool
from Tools.FileReaderTool import FileReaderTool
from Tools.tool_utils.ToolRegistry import ToolRegistry
from Tools.tool_utils.ToolSelector import ToolSelector


class SetupHelper:
    def __init__(self):
        self._setup_steps = []

    def CreateToolRegistry(self) -> ToolSelector:
        registry = ToolRegistry()

        registry.register(CodeGeneratorTool(...))
        registry.register(FileReaderTool(...))
        registry.register(CodeRunnerTool(...))
        registry.register(CreateBranchTool(...))
        registry.register(DiffTool(...))
        registry.register(CreatePRTool(...))

        return ToolSelector(registry)

