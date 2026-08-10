import os
import sys
from typing import List
from Agent.AgentNames import AgentName
from LLM.LLM import LLM
from LLM.LLMCache import LLMCache
from LLM.LLMProvider import LLMProvider
from Orchestration.Orchestrator import Orchestrator
from Tasks.Task import Task
from Tasks.TaskState import State
from Agent.Agents.DeveloperAgent import DeveloperAgent
from Agent.Agents.PlannerAgent import PlannerAgent
from Agent.Agents.ProjectPlannerAgent import ProjectPlannerAgent
from Agent.Agents.ReviewerAgent import ReviewerAgent
from Bootstrap.SetupHelper import SetupHelper
from Tools.Git.GitUtils import GitUtils

def main(args=sys.argv[1:]):
    if len(args) < 1:
        print("Repostory path provided. Using default path: ./")
        cwd = os.getcwd()
        repo_path = os.path.join(cwd, "./")
        task_path = f"{cwd}/Tasks/"
        print(f"Repository path: {repo_path}")
        print(f"Task path: {task_path}")
    else:
        repo_path = args[0]
        task_path = f"{repo_path}/Tasks/"
        print(f"Repository path: {repo_path}")
        print(f"Task path: {task_path}")

    if len(args) < 2:
        print("No prompt provided. Exiting...")
        return
    else:
        prompt = args[1]

    print("Starting AI Agent Orchestrator...")

    skillRegistry = SetupHelper.create_skill_registry()
    toolSelector = SetupHelper.CreateToolRegistry(skillRegistry, repo_path, task_path)
    skillSelector = SetupHelper.create_skill_selector(skillRegistry)
    SetupHelper.setup_utils_with_paths(repo_path, task_path)

    qwen_2_5_coder_7b_instruct_stream = LLM(
        LLMProvider.OLLAMA,
        "qwen2.5-coder:7b",
        isStream=True,
        endpoint="http://localhost:11434",
        cache=LLMCache(),
    )

    agents = {
        AgentName.DEVELOPER: DeveloperAgent(
            llm=qwen_2_5_coder_7b_instruct_stream,
            tool_selector=toolSelector,
            skill_selector=skillSelector,
        ),
        AgentName.PROJECT_PLANNER: ProjectPlannerAgent(
            llm=qwen_2_5_coder_7b_instruct_stream,
            tool_selector=toolSelector,
            skill_selector=skillSelector,
        ),
        AgentName.PLANNER: PlannerAgent(
            llm=qwen_2_5_coder_7b_instruct_stream,
            tool_selector=toolSelector,
            skill_selector=skillSelector,
        ),
        AgentName.REVIEWER: ReviewerAgent(
            llm=qwen_2_5_coder_7b_instruct_stream,
            tool_selector=toolSelector,
            skill_selector=skillSelector,
        ),
    }

    GitUtils.create_repository()

    orchestrator = Orchestrator(agents=agents, task_repo=task_path, max_cycles=50)

    # orchestrator.runProjectPlanner(prompt)
    orchestrator.run_all_ready_tasks(prompt)

    print("\n===== FINISHED =====")
    print(f"project path: {repo_path}")


def all_tasks_finished(tasks: List[Task]) -> bool:
    if not tasks:
        return False

    return all(task.status in State.completed_states() for task in tasks)


if __name__ == "__main__":
    main()
