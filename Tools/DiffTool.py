import subprocess
from Tasks import Task
from Tools import Tool

class DiffTool(Tool):
    def run(self, input: Task) -> dict:
        return {"diff": self.get_diff(input.id)}

    def get_diff(self, task_id):
        branch = f"feature/{task_id}"
        subprocess.run(["git", "checkout", branch])
        diff = subprocess.check_output(["git", "diff", "HEAD"]).decode()
        return diff
    
    
class GetFilesChangedTool(Tool):
    def run(set, input: Task) -> dict:
        result = subprocess.run(
            ["git", "diff", "--name-only"],
            capture_output=True,
            text=True
        )
        return {
            "files_changed": result.stdout.splitlines()
        }
