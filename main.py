import json
import os
from pathlib import Path
import sys
from typing import List
from Agent.AgentNames import AgentName
from Agent.DeveloperAgent import DeveloperAgent
from Agent.ProjectPlannerAgent import ProjectPlannerAgent
from Bootstrap.SetupHelper import SetupHelper
from Orchestration.Orchestrator import Orchestrator
from Tasks.Task import Task
from Agent.DeveloperAgent import DeveloperAgent
from Tasks.TaskState import State


def main(args = sys.argv[1:]):
    if len(args) < 1:
        print("Repostory path provided. Using default path: ./")
        cwd = os.getcwd()
        repo_path = os.path.join(cwd, "./")
        print(f"Repository path: {repo_path}")
        print(f"Task path: {cwd}/Tasks/")
    else:
        repo_path = args[0]
        print(f"Repository path: {repo_path}")
        print(f"Task path: {repo_path}/Tasks/")

    if len(args) < 2:
        print("No prompt provided. Exiting...")
        return
    else:
        prompt = args[1]

    

    print("Starting AI Agent Orchestrator...")

    toolSelector = SetupHelper.CreateToolRegistry()
    skillSelector = SetupHelper.create_skill_selector()

    

    agents = {
        AgentName.DEVELOPER: DeveloperAgent(
            llm="qwen2.5-coder-7b-instruct",
            tool_selector=toolSelector,
            skill_selector=skillSelector
        ),
        AgentName.PROJECT_PLANNER: ProjectPlannerAgent(
            llm="qwen2.5-coder-7b-instruct",
            tool_selector=toolSelector,
            skill_selector=skillSelector
        )
    }

    orchestrator = Orchestrator(
        agents=agents,
        task_repo=f"{repo_path}/Tasks/",
        max_cycles=50
    )

    orchestrator.runProjectPlanner(prompt)

    isComplete = False
    while not isComplete:
        tasks = getAllTasks = load_tasks_from_folder(orchestrator.task_repo)
        isCompplete = all_tasks_finished(tasks)

    print("\n===== FINAL RESULT =====")
    print("Tasks: ", tasks)



def load_tasks_from_folder(path: str) -> List[Task]:
    task_folder = Path(path)

    if not task_folder.exists():
        raise ValueError(
            f"Task folder does not exist: {path}"
        )

    tasks = []

    for file in task_folder.iterdir():

        # Ignore directories
        if not file.is_file():
            continue

        # Only load json task files
        if file.suffix.lower() != ".json":
            continue

        try:
            data = json.loads(
                file.read_text(
                    encoding="utf-8"
                )
            )

            task = Task(**data)

            tasks.append(task)

        except Exception as e:
            raise ValueError(
                f"Failed loading task file {file}: {e}"
            )

    return tasks

def all_tasks_finished(tasks: List[Task]) -> bool:
    if not tasks:
        return False

    finished_states = {
        State.READY_FOR_MERGE,
        State.MERGED,
    }

    return all(
        task.status in finished_states
        for task in tasks
    )

if __name__ == "__main__":
    main()