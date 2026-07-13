from typing import Dict

from Agent.AgentNames import AgentName
from Agent.BaseAgent import BaseAgent
from Agent.ProjectPlannerAgent import ProjectPlannerAgent
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
    def __init__(self, agents:Dict[AgentName, BaseAgent], task_repo, max_cycles=50):
        self.agents = agents
        self.task_repo = task_repo
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

            agent = self.get_agent(task)

            prev_state = task.status

            task = agent.run(task)

            if prev_state == task.status:
                raise Exception(f"No state change detected in {task.status}")

            # 🔒 Validate state transition
            self.validate_transition(prev_state, task.status)

            # 💾 Persist after every step
            self.task_repo.save(task)

            cycles += 1

        if task.status == State.READY_FOR_MERGE:
            print(f"Task {task.id} ready for merge (human step).")
        elif task.status == State.MERGED:
            print(f"Task {task.id} fully completed.")

        return task

    def get_agent(self, task):
        state = task.status
        agent_key = STATE_TO_AGENT.get(state)

        if not agent_key:
            raise Exception(f"No agent mapped for state: {state}")

        agent = self.agents[agent_key]
        agent.prepare(task)

        return agent

    def validate_transition(self, from_state, to_state):
        allowed = ALLOWED_TRANSITIONS.get(from_state, [])

        if to_state not in allowed:
            raise Exception(
                f"Invalid state transition: {from_state} → {to_state}"
            )