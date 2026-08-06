from pathlib import Path
from typing import Dict, List, Optional
from Agent.AgentNames import AgentName
from Agent.BaseAgent import BaseAgent
from Tasks.Task import Task
from Tasks.TaskState import State
from Tools.Task.TaskFileUtils import TaskFileUtils

STATE_TO_AGENT = {
    State.CREATED: AgentName.PLANNER,
    State.READY_FOR_PLANNING: AgentName.PLANNER,
    State.PLANNING: AgentName.PLANNER,
    State.READY_FOR_DEVELOPMENT: AgentName.DEVELOPER,
    State.DEVELOPMENT: AgentName.DEVELOPER,
    State.READY_FOR_REVIEW: AgentName.REVIEWER,
    State.REVIEW: AgentName.REVIEWER,
}

ALLOWED_TRANSITIONS = {
    State.CREATED: [State.READY_FOR_PLANNING],
    State.READY_FOR_PLANNING: [State.PLANNING],
    State.PLANNING: [State.READY_FOR_DEVELOPMENT],
    State.READY_FOR_DEVELOPMENT: [State.DEVELOPMENT],
    State.DEVELOPMENT: [State.READY_FOR_REVIEW],
    State.READY_FOR_REVIEW: [State.REVIEW],
    State.REVIEW: [State.READY_FOR_MERGE, State.READY_FOR_DEVELOPMENT],
}


class Orchestrator:
    def __init__(self, agents: Dict[AgentName, BaseAgent], task_repo, max_cycles=50):
        self.agents = agents
        self.task_repo = Path(task_repo)
        self.max_cycles = max_cycles
        self.tasks = self._load_tasks_from_folder()

    def runProjectPlanner(self, prompt: str):
        projectPlanner = self.agents[AgentName.PROJECT_PLANNER]
        projectPlanner.run(prompt)

    def orchestrate(self, task, prompt: str):
        cycles = 0

        while task.status not in [State.READY_FOR_MERGE, State.MERGED]:
            if cycles > self.max_cycles:
                raise Exception(f"Max cycles exceeded for task {task.id}")

            print(f"[Orchestrator] Current state: {task.status}")

            agent = self._get_agent(task)
            agent.prepare(prompt, task)

            prev_state = task.status

            task = agent.run(task)

            if task.status not in State.active_states() and task.status not in State.completed_states():
                raise Exception(f"Task {task.id} did not transition to an active state: {prev_state}.")

            if prev_state == task.status:
                TaskFileUtils.advance_task_state(task.id)

            if task.status not in State.ready_states() and task.status not in State.completed_states():
                raise Exception(f"Task {task.id} did not transition to a ready state: {prev_state}.")

            # Validate state transition
            self._validate_transition(prev_state, task.status)

            file_path = self.task_repo / f"{task.id}.json"
            json_payload = task.model_dump_json(indent=4)
            file_path.write_text(json_payload, encoding="utf-8")

            cycles += 1

        if task.status == State.READY_FOR_MERGE:
            print(f"Task {task.id} ready for merge (human step).")
        elif task.status == State.MERGED:
            print(f"Task {task.id} fully completed.")

        return task

    def _get_agent(self, task):
        state = task.status
        agent_key = STATE_TO_AGENT.get(state)

        if not agent_key:
            raise Exception(f"No agent mapped for state: {state}")

        agent = self.agents[agent_key]

        return agent

    def _validate_transition(self, from_state, to_state):
        allowed = ALLOWED_TRANSITIONS.get(from_state, [])

        if to_state not in allowed:
            raise Exception(f"Invalid state transition: {from_state} → {to_state}")

    def _get_next_ready_task(self) -> Optional[Task]:
        task = self._get_ready_task()
        if not task: # Reload tasks - if new tasks are created, solve those then complete.
            self.tasks = self._load_tasks_from_folder()
            task = self._get_ready_task()
        if task is not None:
            return task
        
        return None

    def _get_ready_task(self) -> Optional[Task]:
        for task in self.tasks:
            if task.status in State.completed_states():
                self.tasks.remove(task)
                continue
            return task

    def _load_tasks_from_folder(self) -> List[Task]:
        TaskFileUtils.load_all_tasks()
        self.task_repo.mkdir(parents=True, exist_ok=True)
        
        tasks, skipped_files = TaskFileUtils.load_all_tasks()

        return tasks

    def run_all_ready_tasks(self, prompt: str):
        while True:
            task = self._get_next_ready_task()

            if not task:
                print("No more ready tasks.")
                break

            print(f"Running task {task.id}...")
            self.orchestrate(task, prompt)
