import subprocess
from Tools import Tool


class CreatePRTool(Tool):
    def run(self, input: dict) -> dict:
        branch_name = input.get("branch_name")
        pr_title = input.get("pr_title")
        pr_description = input.get("pr_description")
        
        subprocess.run(f"git checkout {branch_name}")
        subprocess.run(f"git push origin {branch_name}")
        subprocess.run(f"gh pr create --title '{pr_title}' --body '{pr_description}' --base main --head {branch_name}")
        
        return {"status": "success", "message": f"Pull request for branch '{branch_name}' created successfully."}