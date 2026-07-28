import inspect
import importlib
import importlib.util
from pathlib import Path
import sys
from types import ModuleType
from typing import List
from pydantic import BaseModel
from Tools.Tool import Tool


class ToolDiscovery:
    @staticmethod
    def discover_tools(base_dir: Path) -> List[Tool]:
        tools = ToolDiscovery.__get_tools(base_dir)
        return tools
    
    # @staticmethod
    # def __get_tools(base_path: Path) -> List[Tool]:
    #     tools: List[Tool] = []
        
    #     for file_path in base_path.rglob("*.py"):
    #         if file_path.name == "Tool.py" or "tool_utils" in file_path.parts:
    #             continue
                
    #         try:
    #             # module_name = file_path.stem 
    #             relative_path = file_path.relative_to(base_path.parent)
    #             module_name = ".".join(relative_path.with_suffix("").parts)
                
    #             spec = importlib.util.spec_from_file_location(module_name, str(file_path))
    #             if spec is None or spec.loader is None:
    #                 continue
                    
    #             module = importlib.util.module_from_spec(spec)
    #             sys.modules[module_name] = module

    #             spec.loader.exec_module(module)
    #             ## TODO DELETE:
    #             for name in sys.modules:
    #                 if "LoadSkillTool" in name:
    #                     print(name)
    #             ## TODO DELETE:

    #             tool = ToolDiscovery.__get_tool_in_module(module)
    #             if(tool is not None):
    #                 tools.append(tool)
                
    #         except Exception as import_error:
    #             print(f"[ToolDiscovery] Warning: Failed to import {file_path}: {import_error}")
                
    #     return tools

    @staticmethod
    def __get_tools(base_path: Path) -> List[Tool]:
        tools = []

        for file_path in base_path.rglob("*.py"):
            if file_path.name == "Tool.py" or "tool_utils" in file_path.parts:
                continue

            try:
                relative_path = file_path.relative_to(base_path.parent)
                module_name = ".".join(relative_path.with_suffix("").parts)

                module = importlib.import_module(module_name)

                tool = ToolDiscovery.__get_tool_in_module(module)

                if tool is not None:
                    tools.append(tool)

            except Exception as e:
                print(f"Failed loading {file_path}: {e}")

        # print("----- Tool Discovery tools: ----- ")
        # for tool in tools:
        #     print(f"- {tool.name}")
        # print("----- END ----- ")

        return tools

    
    @staticmethod
    def __get_tool_in_module(module: ModuleType) -> Tool | None:
        for _, obj in inspect.getmembers(module):
            if (
                inspect.isclass(obj)
                and issubclass(obj, Tool)
                and obj is not Tool
            ):
                try:
                    tool_kwargs = ToolDiscovery.__get_tool_args(obj)
                    tool_instance = obj(**tool_kwargs)
                    return tool_instance
                except Exception as e:
                    print(
                        f"[ToolDiscovery] Warning: Skipping configuration for tool '{obj.__name__}': {e}"
                    )

    @staticmethod
    def __get_tool_args(obj: type[Tool]) -> dict:
        tool_kwargs = {}
        fields_to_extract = ["name", "description", "tags", "capabilities", "path", "input_model"]

        for field in fields_to_extract:
            if field in obj.model_fields:
                default_value = obj.model_fields[field].default
                
                if default_value.__class__.__name__ == "PydanticUndefined":
                    tool_kwargs[field] = "" if field in ["name", "description", "path"] else []
                else:
                    tool_kwargs[field] = default_value
            else:
                tool_kwargs[field] = BaseModel if field == "input_model" else ("" if field in ["name", "description", "path"] else [])
        return tool_kwargs

