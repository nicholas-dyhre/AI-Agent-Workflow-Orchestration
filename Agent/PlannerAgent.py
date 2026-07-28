import json
from Agent.BaseAgent import BaseAgent
from Agent.AgentNames import AgentName
from Agent.AgentResponse import AgentResponse
from Tasks.Task import Task
from LLM.LLM import LLM
from Skills.skill_utils.SkillSelector import SkillSelector
from Tools.tool_utils.ToolCapability import ToolCapability
from Tools.tool_utils.ToolSelector import ToolSelector
from Tools.tool_utils.ToolTag import ToolTag


class PlannerAgent(BaseAgent):
    def __init__(self, llm: LLM, tool_selector: ToolSelector, skill_selector: SkillSelector):
        super().__init__(llm, tool_selector, skill_selector)
        self.name = AgentName.PLANNER.value
        self.agentName = AgentName.PLANNER
        self.allowed_tags.extend([ToolTag.TASKS, ToolTag.PERSISTENCE, ToolTag.FILESYSTEM, ToolTag.QUERY])
        self.allowed_capabilities.extend([ToolCapability.MODIFY_TASKS, ToolCapability.WRITE_TASK_LOGS, ToolCapability.SAVE_TASKS, ToolCapability.VALIDATE_TASKS])

    def run(self, task: Task) -> Task:
        self.prepare(task)

        if task.plan:
            print(f"Task {task.id} already has a plan. Skipping planning.")
            return task

        print(f"[{self.name}] Initiating ReAct plan generation loop for: {task.title}")

        # Execute the stream. The agent will call the PatchTaskTool internally.
        final_response: AgentResponse = self.execute_plan_generation(task)

        patched_task = self._reload_task(task.id)

        self.log(
            patched_task,
            input=task.description,
            output=f"Planner completed execution. Plan now contains {len(patched_task.plan)} steps.",
        )

        return patched_task

    def execute_plan_generation(self, task: Task) -> AgentResponse:
        prompt = self.build_prompt(task)

        # Inject context instructing the model to use the tool instead of raw text returns
        planning_instruction = (
            f"\n\nCRITICAL INSTRUCTION: You must decompose this task into a sequential list of steps. "
            f"You are REQUIRED to use the 'patch_task' tool to save this plan before stopping.\n\n"
            f"When calling the 'patch_task' tool, use these exact parameters:\n"
            f"- 'task_id': '{task.id}'\n"
            f"- 'updates': A JSON object matching the schema definitions outlined below:\n\n"
            f"{self.get_patch_plan_schema()}\n\n"
            f"Ensure each step object in your array generates a unique 'id' tracking token, "
            f"formatted precisely as: '{task.id}_step_1', '{task.id}_step_2', etc.\n"
            f"Once you receive a successful confirmation from the 'patch_task' tool, "
            f"you may call your 'final' action to conclude."
        )

        response = self.ReActObs_stream(prompt + planning_instruction)
        return response

    def get_patch_plan_schema(self) -> str:
        # Pull definitions directly from Task to avoid hardcoding enum options
        full_schema = Task.model_json_schema()

        patch_schema = {
            "type": "object",
            "required": ["plan"],
            "properties": {"plan": full_schema["properties"]["plan"]},
            "$defs": full_schema.get("$defs", {}),
        }
        return json.dumps(patch_schema, indent=4)

    def _reload_task(self, task_id: str) -> Task:
        # Helper to read back the updated state from disk
        # Adjust the folder path if your environment uses a non-default base directory
        import os

        file_path = f"tasks/{task_id}.json"
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                return Task.model_validate_json(f.read())
        raise RuntimeError(f"Could not reload patched task file for id: {task_id}")
