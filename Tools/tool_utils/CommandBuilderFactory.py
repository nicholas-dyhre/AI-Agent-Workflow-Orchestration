import json
from pathlib import Path
from Tools.tool_utils.ExecutableProjectCommand import ExecutableProjectCommand
from Tools.tool_utils.FrameworkIdentifiers import Framework, FrameworkIdentifiers

class CommandBuilder:
    def __init__(self, target: Path, framework: Framework):
        self.target: Path = target
        self.framework: Framework = framework
        
    def build(self) -> ExecutableProjectCommand:
        raise NotImplementedError("Not implemented")
        
    def verify_file(self) -> bool:
        if not self.target.exists():
            print(f"The project path or file {self.target} does not exist")
            return False
        return True

class JavascriptBuilder(CommandBuilder):
    def build(self) -> ExecutableProjectCommand:
        target_file = (self.target / "package.json")
        if not (target_file).is_file():
            raise Exception("Could not verify file")
        try:
            content = self.target.read_text(encoding="utf-8")
            pkg = json.loads(content)
            scripts = pkg.get("scripts", {})
            
            if not isinstance(scripts, dict):
                raise Exception("Scripts block in package.json is not a valid JSON object")

            cmd_map = {"build": "", "start": "", "test": "", "dev": ""}
            for key, val in scripts.items():
                for target_action in cmd_map.keys():
                    if not cmd_map[target_action] and target_action in key:
                        cmd_map[target_action] = val

            return ExecutableProjectCommand(
                framework=self.framework,
                working_dir=self.target,
                build_cmd=cmd_map["build"],
                run_cmd=cmd_map["start"],
                test_cmd=cmd_map["test"],
                dev_run_cmd=cmd_map["dev"]
            )
        except Exception as e:
            raise Exception(f"Could not parse package.json: {e}")

class PythonBuilder(CommandBuilder):
    def build(self) -> ExecutableProjectCommand:
        if not self.verify_file():
            raise Exception("Could not verify directory")
        
        run_cmd = "python main.py" if (self.target / "main.py").is_file() else "python -m src"
        test_cmd = "pytest" if (self.target / "pytest.ini").is_file() else "python -m unittest"
            
        return ExecutableProjectCommand(
            framework=self.framework,
            working_dir=self.target,
            build_cmd="",
            run_cmd=run_cmd,
            test_cmd=test_cmd,
            dev_run_cmd=run_cmd
        )

class DotNetBuilder(CommandBuilder):
    def build(self) -> ExecutableProjectCommand:
        if not self.verify_file():
            raise Exception("Could not verify directory")

        return ExecutableProjectCommand(
            framework=self.framework,
            working_dir=self.target,
            build_cmd="dotnet build",
            run_cmd="dotnet run",
            test_cmd="dotnet test",
            dev_run_cmd="dotnet watch",
        )

class CommandBuilderFactory:
    @classmethod
    def GetBuilders(cls, targets: list[Path]) -> list[CommandBuilder]:
        command_builders: list[CommandBuilder] = []
        for target in targets:
            builder = cls.GetBuilder(target)
            if builder:
                command_builders.append(builder)
        return command_builders

    @classmethod
    def GetBuilder(cls, target: Path) -> CommandBuilder | None:
        if any(k in target.name.lower() for k in ["node_modules", "venv", "env", "test", "asset", "docs"]):
            return None
        framework = FrameworkIdentifiers.getFrameworkFromFileIndicator(target)
        if framework is None:
            return None
        match framework:
            case Framework.Python:
                return PythonBuilder(target, Framework.Python)
            case Framework.Dotnet:
                return DotNetBuilder(target, Framework.Dotnet)
            case Framework.Javascript:
                return JavascriptBuilder(target, Framework.Javascript)
            # case Framework.Go:
            #     return GoBuilder(target)
            case _:
                raise Exception(f"Builder for this framework is not implemented")
        # if (target / "package.json").is_file():
        #     return JavascriptBuilder(target)
            
        # if target.is_dir():
        #     if (target / "requirements.txt").is_file() or (target / "pyproject.toml").is_file() or list(target.glob("*.py")):
        #         return PythonBuilder(target)
                
        #     if list(target.glob("*.csproj")) or list(target.glob("*.sln")):
        #         return DotNetBuilder(target)
                
        return None
