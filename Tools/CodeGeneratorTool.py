from Tools import Tool


class CodeGeneratorTool(Tool):
    def run(self, input: CodeGenInput):
        return {
            "diff": self.llm(f"Generate patch for: {input.instructions}")
        }