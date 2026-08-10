# from Agent.Utils.AgentInputCleaner import clean_and_parse_json
# from Agent.Utils.Formatters import format_custom_structure
# from Agent.Utils.Formatters import _to_run_time_executions
# from Agent.Utils.Formatters import format_planstep
# from Agent.Utils.Formatters import All

# import inspect
# from .AgentInputCleaner import clean_and_parse_json
# from . import Formatters

# __all__ = ["clean_and_parse_json"]

# for name, obj in inspect.getmembers(Formatters):
#     if inspect.isfunction(obj):
#         globals()[name] = obj
#         __all__.append(name)


# __all__ = [
#     "format_planstep",
#     "format_task",
#     "format_tools",
#     "format_skills",
#     "format_goal_checker_tools",
# ]

import tiktoken
from .Formatters import *
from .AgentInputCleaner import clean_and_parse_json

def count_tokens(text: str, model: str = "gpt-4o-mini") -> int:
    encoding = tiktoken.get_encoding("cl100k_base")
    # encoding = tiktoken.encoding_for_model(model)
    tokens = encoding.encode(text)
    return len(tokens)


# clean_and_parse_json = clean_and_parse_json
# format_custom_structure = format_custom_structure
# _to_run_time_executions = _to_run_time_executions
# format_planstep = format_planstep

# for item in All:
#     item = item
