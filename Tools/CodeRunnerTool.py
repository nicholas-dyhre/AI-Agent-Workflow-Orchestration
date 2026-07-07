import subprocess
from Tools import Tool


class CodeRunnerTool(Tool):
    def run(self, input):
        result = subprocess.run(
            input.command,
            capture_output=True,
            text=True
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0
        }