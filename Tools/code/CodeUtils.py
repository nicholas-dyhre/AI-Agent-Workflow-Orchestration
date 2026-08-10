
import logging
import subprocess
from pathlib import Path
from typing import ClassVar, Optional
from Tools.tool_utils.CommandBuilderFactory import CommandBuilderFactory
from Tools.tool_utils.ExecutableProjectCommand import ExecutableProjectCommand, ProjectRunOutput

logger = logging.getLogger(__name__)

class CodeUtils:
    _repo_base_path: ClassVar[Optional[Path]] = None
    _active_processes: ClassVar[dict[str, subprocess.Popen]] = {}

    @classmethod
    def set_base_path(cls, path: str | Path) -> None:
        """Sets the absolute base directory of the code repository."""
        cls._repo_base_path = Path(path).resolve()

    @classmethod
    def _get_configured_path(cls, ) -> Path:
        if cls._repo_base_path is None:
            raise ValueError(
                "CodeUtils base path has not been configured. "
                "Call CodeUtils.set_base_path() before executing operations."
            )
        return cls._repo_base_path

    @classmethod
    def _safe_resolve(cls, sub_path: str | Path | None = None) -> Path:
        """
        Resolves a sub-path relative to the repository base path.
        Prevents directory traversal attacks (e.g., passing '../../etc/passwd').
        """
        base = cls._get_configured_path()
        if sub_path is not None:
            try:
                target = (base / sub_path).resolve()
                if not target.is_relative_to(base):
                    raise PermissionError(
                        f"Access denied: Target path '{sub_path}' is outside the repository boundary."
                    )
                return target
            except Exception as e: 
                raise Exception(f"Could not combine path and relative dir. {e}"
            )

        return base

    @classmethod
    def read_file(cls, sub_path: str, start_line: Optional[int] = None, end_line: Optional[int] = None) -> tuple[bool, str]:
        """
        Reads a file. Supports line pagination to protect agent context windows.
        Line numbers are 1-indexed (inclusive).
        """
        path = cls._safe_resolve(sub_path)
        if not path.is_file():
            return False, f"File not found at '{sub_path}'"

        try:
            lines = path.read_text(encoding="utf-8").splitlines()
            total_lines = len(lines)

            if start_line is not None or end_line is not None:
                start = max(1, start_line if start_line else 1) - 1
                end = min(total_lines, end_line if end_line else total_lines)
                sliced_lines = lines[start:end]
                
                content = "\n".join(f"{idx + start + 1}: {line}" for idx, line in enumerate(sliced_lines))
                return True, f"[Showing lines {start + 1} to {end} of {total_lines} from {sub_path}]\n{content}"
            
            return True, path.read_text(encoding="utf-8")
        except Exception as e:
            return False, f"Error reading file '{sub_path}': {str(e)}"

    @classmethod
    def write_file(cls, sub_path: str, content: str) -> tuple[bool, str]:
        """Overwrites or creates a file with complete content."""
        path = cls._safe_resolve(sub_path)
        if not path.suffix.lower():
            return (False, f"Sub_path ('{sub_path}') is missing file extension.")
        try:
            path.parent.mkdir(parents=True, exist_ok=True)

            # if not path.is_file():
            #     return (False, f"Error writing because '{sub_path}' is not a file")

            path.write_text(content, encoding="utf-8")
            return (True, f"Wrote {len(content.splitlines())} lines to '{sub_path}'.")
        except Exception as e:
            return (False, f"Error writing to file '{sub_path}': {str(e)}")

    @classmethod
    def run_process(cls, command: list[str], sub_path: str | None = None, timeout: int = 30) -> tuple[int, str, str]:
        """Run a console command"""
        try:
            path = cls._safe_resolve(sub_path)
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=30,
                cwd=str(path)
            )
            return (result.returncode, result.stdout, result.stderr)

        except Exception as e:
            return (1, "", f"{str(e)}")

    @classmethod
    def create_directory(cls, sub_path: str) -> tuple[bool, str]:
        """Creates a directory at the specified sub-path, including any missing parent folders."""
        try:
            path = cls._safe_resolve(sub_path)
            if path.exists():
                if path.is_dir():
                    return (True, f"Notice: Directory '{sub_path}' already exists.")
                else:
                    return (False, f"Error: Cannot create directory because a file already exists at '{sub_path}'.")
            path.mkdir(parents=True, exist_ok=True)
            return (True, sub_path)
            
        except Exception as e:
            return (False, f"Error creating directory at '{sub_path}': {str(e)}")


    @classmethod
    def patch_file(cls, sub_path: str, search_string: str, replace_string: str) -> tuple[bool, str]:
        """
        Performs a search-and-replace edit. This is the preferred method for agents 
        to edit code without rewriting whole blocks and risking formatting breakage.
        """
        path = cls._safe_resolve(sub_path)
        if not path.is_file():
            return (False, f"Error: File '{sub_path}' does not exist.")

        try:
            content = path.read_text(encoding="utf-8")
            if search_string not in content:
                return (False, f"Error: Could not find exact match for search_string in '{sub_path}'. No changes made.")
            
            if content.count(search_string) > 1:
                return (False, f"Error: Multiple matches found for search_string in '{sub_path}'. Be more specific.")

            new_content = content.replace(search_string, replace_string)
            path.write_text(new_content, encoding="utf-8")
            return (True, f"Success: Successfully updated '{sub_path}'.")
        except Exception as e:
            return (False, f"Error patching file '{sub_path}': {str(e)}")

    @classmethod
    def _get_gitignore_matcher(cls) -> list[str]:
        """
        Reads the root .gitignore file if it exists and returns a list of patterns.
        Always includes universal fallback patterns to keep the environment stable.
        """
        patterns = [".git", "__pycache__", "node_modules", ".venv", "env", "*.pyc"]
        
        try:
            gitignore_path = cls._safe_resolve(".gitignore")            
            if gitignore_path.is_file():
                for line in gitignore_path.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line and not line.startswith("#"):
                        patterns.append(line.rstrip("/"))
        except Exception as e:
            logger.warning(f"Could not parse .gitignore, falling back to defaults: {e}")
            
        return list(set(patterns))

    @classmethod
    def list_files(cls, sub_path: str | None, max_depth: int = 3, folders_to_skip: list[str] = []) -> tuple[bool, str]:
        """
        Lists files in a tree-like structure. 
        Dynamically filters out clutter based on the repository's .gitignore configurations.
        Returns a tuple of (success: bool, output: str).
        """
        import fnmatch

        try:
            root = cls._safe_resolve(sub_path)
            if not root.exists():
                return False, f"Error: The directory path '{sub_path}' does not exist."
            if not root.is_dir():
                return False, f"Error: The path '{sub_path}' exists but is a file, not a directory."

            if folders_to_skip is None:
                folders_to_skip = []

            ignore_patterns = cls._get_gitignore_matcher()
            output = []

            def _should_ignore(name: str) -> bool:
                return any(fnmatch.fnmatch(name, pattern) for pattern in ignore_patterns)

            def _build_tree(current_dir: Path, depth: int):
                if depth > max_depth:
                    return
                try:
                    for entry in sorted(current_dir.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower())):
                        # Skip the folder entirely if its name is in the skip list
                        if entry.is_dir() and entry.name in folders_to_skip:
                            continue
                            
                        if _should_ignore(entry.name):
                            continue
                        
                        indent = "  " * depth
                        
                        if entry.is_dir():
                            output.append(f"{indent}📁 {entry.name}/")
                            _build_tree(entry, depth + 1)
                        else:
                            output.append(f"{indent}📄 {entry.name}")
                except PermissionError:
                    pass

            _build_tree(root, 0)
            if output:
                return True, "\n".join(output)
            else:
                return True, f"No files found in '{sub_path}'."
                
        except Exception as e:
            return False, f"Error listing files: {str(e)}"

    @classmethod
    def _infer_project_commands(cls, relative_dir: str | Path | None = None) -> list[ExecutableProjectCommand]:
        """
        Scans the root and level-1 subdirectories to discover active components.
        Returns a coherent list of CommandUtils instances with a unified schema.
        """
        base = cls._safe_resolve(relative_dir)
        targets = [base] + [d for d in base.iterdir() if d.is_dir() and not d.name.startswith('.')]
        builders = CommandBuilderFactory.GetBuilders(targets)
        project_commands = [builder.build() for builder in builders]
        return project_commands

    @classmethod
    def run_tests(cls, relative_dir: str | Path | None) -> list[ProjectRunOutput]:
        """Executes targeted test suites, filtering logs down to the core trace failures."""        
        try:
            project_commands = cls._infer_project_commands(relative_dir)
            project_run_outputs = [cmd.test() for cmd in project_commands]
            return project_run_outputs
        except subprocess.TimeoutExpired:
            raise Exception("Failed to run command with the timeout")
        except Exception as e:
            raise Exception(f"Failed to run tests: {str(e)}")

    @classmethod
    def run_build(cls, relative_dir: str | Path | None) -> list[ProjectRunOutput]:
        """Executes targeted build"""        
        try:
            project_commands = cls._infer_project_commands(relative_dir)
            project_run_outputs = [cmd.build() for cmd in project_commands]
            return project_run_outputs
        except subprocess.TimeoutExpired:
            raise Exception("Failed to run command with the timeout")
        except Exception as e:
            raise Exception(f"Failed to run buld: {str(e)}")

    @classmethod
    def run_project(cls, relative_dir: str | Path | None) -> list[ProjectRunOutput]:
        """Executes targeted build"""        
        try:
            project_commands = cls._infer_project_commands(relative_dir)
            project_run_outputs = [cmd.run() for cmd in project_commands]
            return project_run_outputs
        except subprocess.TimeoutExpired:
            raise Exception("Failed to run command with the timeout")
        except Exception as e:
            raise Exception(f"Failed to run project: {str(e)}")

    @classmethod
    def run_dev(cls, relative_dir: str | Path | None) -> list[ProjectRunOutput]:
        """Executes targeted build"""        
        try:
            project_commands = cls._infer_project_commands(relative_dir)
            project_run_outputs = [cmd.dev() for cmd in project_commands]
            return project_run_outputs
        except subprocess.TimeoutExpired:
            raise Exception("Failed to run command with the timeout")
        except Exception as e:
            raise Exception(f"Failed to run dev project: {str(e)}")