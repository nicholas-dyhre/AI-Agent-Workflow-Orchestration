import inspect
import importlib
import pkgutil

from Tools.Tool import Tool


class ToolDiscovery:

    @staticmethod
    def discover_tools(package_name: str):

        tools = []

        package = importlib.import_module(package_name)

        for _, module_name, _ in pkgutil.iter_modules(package.__path__):

            # Skip utils
            if module_name.startswith("tool_utils"):
                continue

            module = importlib.import_module(
                f"{package_name}.{module_name}"
            )

            for _, obj in inspect.getmembers(module):

                if (
                    inspect.isclass(obj)
                    and issubclass(obj, Tool)
                    and obj is not Tool
                ):
                    tools.append(obj)

        return tools