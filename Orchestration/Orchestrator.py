import json
from pathlib import Path
from typing import Dict, List, Optional
from Agent.AgentNames import AgentName
from Agent.BaseAgent import BaseAgent
from Tasks.Task import Task
from Tasks.TaskState import State

STATE_TO_AGENT = {
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

    def runProjectPlanner(self, prompt: str):
        projectPlanner = self.agents[AgentName.PROJECT_PLANNER]
        projectPlanner.run(prompt)

    def orchestrate(self, task):
        cycles = 0

        while task.status not in [State.READY_FOR_MERGE, State.MERGED]:
            if cycles > self.max_cycles:
                raise Exception(f"Max cycles exceeded for task {task.id}")

            print(f"[Orchestrator] Current state: {task.status}")

            agent = self._get_agent(task)
            agent.prepare(task)

            prev_state = task.status

            task = agent.run(task)

            if prev_state == task.status:
                raise Exception(f"No state change detected in {task.status}")

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
        agent.prepare(task)

        return agent

    def _validate_transition(self, from_state, to_state):
        allowed = ALLOWED_TRANSITIONS.get(from_state, [])

        if to_state not in allowed:
            raise Exception(f"Invalid state transition: {from_state} → {to_state}")

    def _get_next_ready_task(self) -> Optional[Task]:
        tasks: List[Task] = self._load_tasks_from_folder()

        task_map = {task.id: task for task in tasks}

        for task in tasks:
            if task.status in State.completed_states():
                continue

            dependencies = task.metadata.get("dependencies", [])

            if all(
                task_map[d].status in State.completed_states()
                for d in dependencies
                if d in task_map
            ):
                return task

        return None

    def _load_tasks_from_folder(self) -> List[Task]:
        self.task_repo.mkdir(parents=True, exist_ok=True)
        
        tasks: List[Task] = []

        for file in self.task_repo.iterdir():
            if not file.is_file():
                continue

            if file.suffix.lower() != ".json":
                continue

            try:
                data = json.loads(file.read_text(encoding="utf-8"))
                task: Task = Task(**data)
                tasks.append(task)
            except Exception as e:
                raise ValueError(f"Failed loading task file {file}: {e}")

        return tasks

    def run_all_ready_tasks(self):
        while True:
            task = self._get_next_ready_task()

            if not task:
                print("No more ready tasks.")
                break

            print(f"Running task {task.id}...")
            self.orchestrate(task)
