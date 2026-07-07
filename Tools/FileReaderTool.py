from Tools import Tool


class FileReaderTool(Tool):
    def run(self, input):
        with open(input.path, "r") as f:
            return {"content": f.read()}