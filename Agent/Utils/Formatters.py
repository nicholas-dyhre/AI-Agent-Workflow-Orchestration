from pathlib import Path
from typing import Any, Callable, Type

from Agent.AgentNames import AgentName
from Agent.AgentResponse import AgentAction, AgentResponse
from Skills.skill_utils.SkillNode import SkillNode
from Tasks.Task import PlanStep, Task
from Tools.Tool import Tool, ToolResult
from Common.color_printer import error, info, success, wild


def format_custom_structure(data: Any) -> str:
    # 1. Handle Dictionaries
    if isinstance(data, dict):
        items = []
        for k, v in data.items():
            formatted_val = format_custom_structure(v)
            items.append(f"{k}: {formatted_val}")
        return "{" + ", ".join(items) + "}"
    
    # 2. Handle Lists
    elif isinstance(data, list):
        items = [format_custom_structure(item) for item in data]
        return "[" + ", ".join(items) + "]"
    
    # 3. Handle Booleans (Must check before int, because bool is a subclass of int)
    elif isinstance(data, bool):
        return "True" if data else "False"
    
    # 4. Handle Path Objects
    elif isinstance(data, Path):
        return f'"{data.as_posix()}"'
    
    # 5. Handle Strings
    elif isinstance(data, str):
        cleaned_str = data.replace("\n", "")
        return f'"{cleaned_str}"'
    
    # 6. Fallback for other primitive types (int, float, None, etc.)
    return str(data)

def to_run_time_executions(result: ToolResult, step: int, agentResponse: AgentResponse) -> str:
    """Formats a runtime execution step into a structured logging/prompt string."""
    action = agentResponse.action
    base_step = f"Step: {step}:"

    # Handle Final Response
    if action == AgentAction.Final.value:
        return f"{base_step} Final Response `{agentResponse.final_answer}`"

    # Handle Errors / Bad Actions
    if action != AgentAction.Tool.value:
        return f"{base_step} ERROR! Agent provided bad action: {action}"

    # Handle Tool Execution
    tool_call = f"{base_step} Tool called `{agentResponse.tool_name}` with input {format_custom_structure(agentResponse.input)}"

    if result.data:
        if output := result.data.to_string():
            return f"{tool_call} | Action result: \n{output}"
        
        success = "Success" if result.data.success else "Failed"
        return f"{tool_call}Result: {success} | message: {result.data.message or ''}"

    if result.error:
        error_msg = result.error.error or ""
        return f"{tool_call}Result: Failed | message: {error_msg}"

    return f"{tool_call}Result: Unknown | message: No data or error returned"

def print_run_time_executions(result: ToolResult, step: int, agentResponse: AgentResponse) -> None:
    printer = get_printer_for_tool_executions(result)
    printer(to_run_time_executions(result, step, agentResponse))
    # if result and result.data and result.data.success == False:
    #     info(to_run_time_executions(result, step, agentResponse))
    # elif result and not result.data and result.error:
    #     error(to_run_time_executions(result, step, agentResponse))
    # elif result and result.data and result.data.success == True:
    #     success(to_run_time_executions(result, step, agentResponse))
    # else:
    #     wild(to_run_time_executions(result, step, agentResponse))

def get_printer_for_tool_executions(result: ToolResult) -> Callable:
    if result and result.data and result.data.success == False:
        return info
    elif result and not result.data and result.error:
        return error
    elif result and result.data and result.data.success == True:
        return success
    else:
        return wild

def format_planstep(planStep: PlanStep):
        planstep_formatted_to_prompt = planStep.to_prompt()
        # print(f"PlanStep tokens: {self.count_tokens(planstep_formatted_to_prompt, self.llm.model)}")
        return planstep_formatted_to_prompt

def format_task(agentName: AgentName, task: Task):
    task_formatted_to_prompt = task.to_prompt(agentName)
    # print(f"Task tokens: {self.count_tokens(task_formatted_to_prompt, self.llm.model)}")
    return task_formatted_to_prompt

def format_tools(tools: dict):
    tool_formatted_to_prompt = "\n".join([tool.format_for_llm() for tool in tools.values()])
    # print(f"Tools tokens: {self.count_tokens(tool_formatted_to_prompt, self.llm.model)}")
    return tool_formatted_to_prompt

def format_skills(skills: list[SkillNode]):
    skills_formatted_to_prompt = "\n\n".join([f"## Skill: {skill.name}\n{skill.load(True)}" for skill in skills])
    # print(f"skills tokens: {self.count_tokens(skills_formatted_to_prompt, self.llm.model)}")
    return skills_formatted_to_prompt

def format_goal_checker_tools(goal_checker_tools: list[Type[Tool]]):
    formatted_output = " and ".join(
        f"`{tool.name}`" if hasattr(tool, "name") else f"`{tool.__name__}`" 
        for tool in goal_checker_tools
    )
    return formatted_output

def format_skill_options(allowed_skill_nodes: list[SkillNode]):
    all_allowed_names: set[str] = set()
    all_allowed_keywords: set[str] = set()
    for node in allowed_skill_nodes:
        all_allowed_keywords.update(node.keywords)
        all_allowed_names.add(node.name)

    keywords = " | ".join(sorted(all_allowed_keywords))
    names = " | ".join(sorted(all_allowed_names))

    return (
        f"skill_names options for the LoadSkillTool: \n"
        f"{names} \n"
        f"skill_keywords options for the LoadSkillTool: \n"
        f"{keywords}"
        "\n\n"
    )