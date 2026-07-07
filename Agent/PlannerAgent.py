from Agent import BaseAgent
from Tasks import Task

class PlannerAgent(BaseAgent):
    def run(self, task: Task) -> Task:
       prompt = f"""
You are a planner agent responsible for creating a detailed plan to accomplish the following task:
Title: {task.title}
Description: {task.description}"""
       
       response = self.llm(prompt)
       steps = parse_plan(response)
       task.plan = steps
       self.log(task, prompt, response)
    
       return task