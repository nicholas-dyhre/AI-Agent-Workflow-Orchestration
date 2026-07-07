from Agent import BaseAgent
from Tasks import Task

class TesterAgent(BaseAgent):
    def run(self, task: Task) -> Task:
        prompt = f"""
You are a tester agent responsible for testing the following task:
Title: {task.title}
Description: {task.description}"""
       
        latest_diff = task.code_changes[-1]
        result = self.tools['tester'].run(latest_diff.diff)
        if(result['passed']):
            task.status = "Completed"
        else:
            task.status = "Failed"

        self.log(task, prompt, f"Test result: {result['passed']}")
        return task