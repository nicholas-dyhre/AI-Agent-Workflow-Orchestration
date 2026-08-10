from dataclasses import dataclass
from pathlib import Path
import re
import subprocess
from typing import Callable

from Tools.tool_utils.FrameworkIdentifiers import Framework, FrameworkIdentifiers


@dataclass
class CommandRunOutput:
    args: str | list[str]
    stderr: str | None
    stdout: str | None
    returncode: int | None

    def is_success(self) -> bool:
        if self.returncode is None:
            return False
        return self.returncode == 0


@dataclass
class ProjectRunOutput:
    project_command: "ExecutableProjectCommand"
    command_used: str | None
    test_coverage: int | None = None
    test_failed: str | None = None
    execution_output: CommandRunOutput | None = None

    def summarize(self) -> tuple[str, str]:
        message = ""
        summary = ""
        identifier = f"{self.project_command.framework} on path: {self.project_command.working_dir}"

        if not self.execution_output:
            message += f"No output for: {identifier} \n"
            return message, summary

        message += f"Success for: {identifier}\n"
        summary = f"output for {identifier} | "
        summary += f"stdout: {self.execution_output.stdout} \n" if self.execution_output.is_success() else f"stderr: {self.execution_output.stderr} \n"
    
        return message, summary

    def summarize_tests(self) -> str:
        identifier = f"{self.project_command.framework} on path: {self.project_command.working_dir}"
        summary = identifier + "\n"
        summary += f"Test coverage: {self.test_coverage}" if self.test_coverage else "Test coverage is 0, indicating no tests exists, or execution error"
        summary += f"Tests failed:\n{self.test_failed}\n" if self.test_failed else "No tests failure registered"
        return summary


class ExecutableProjectCommand:
    """
    An executable value object containing pre-configured infrastructure actions
    that carry their context natively without requiring manual path arguments.
    """
    def __init__(
        self,
        framework: Framework,
        working_dir: Path,
        build_cmd: str | None = None,
        run_cmd: str | None = None,
        test_cmd: str | None = None,
        dev_run_cmd: str | None = None
    ):
        self.framework = framework
        self.working_dir = working_dir
        self.build_cmd = build_cmd
        self.run_cmd = run_cmd
        self.test_cmd = test_cmd
        self.dev_run_cmd = dev_run_cmd

    def _run_subprocess_wrapper(self, cmd: str, timeout: int) -> CommandRunOutput:
        """Internal physical command execution layer using subprocess.run."""
        try:
            res = subprocess.run(
                cmd,
                shell=True,
                cwd=str(self.working_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout
            )
        except subprocess.TimeoutExpired:
            raise Exception("Failed to run command with the timeout")
        except Exception as e:
                raise Exception(e)
        return CommandRunOutput(args=cmd, stderr=res.stderr, stdout=res.stdout, returncode=res.returncode)

    def _execute_command(
        self, 
        cmd: str | None, 
        timeout_seconds: int, 
        post_processor: Callable[[CommandRunOutput, ProjectRunOutput], None] | None = None
    ) -> ProjectRunOutput:
        """Abstracted master controller managing error handling and response generation."""
        if not cmd:
            return ProjectRunOutput(project_command=self, command_used=cmd)

        try:
            execution_output = self._run_subprocess_wrapper(cmd, timeout_seconds)
        except Exception as e:
            execution_output = CommandRunOutput(
                args=cmd,
                stderr=f"Execution Status: ERROR (System error executing command: {str(e)})",
                stdout="",
                returncode=-1
            )

        output = ProjectRunOutput(
            project_command=self,
            command_used=cmd,
            execution_output=execution_output
        )

        # Execute custom processing hooks if supplied (used for testing anomalies)
        if post_processor and execution_output.returncode != -1:
            post_processor(execution_output, output)

        return output


    def build(self, timeout_seconds: int = 30) -> ProjectRunOutput:
        return self._execute_command(self.build_cmd, timeout_seconds)

    def run(self, timeout_seconds: int = 30) -> ProjectRunOutput:
        return self._execute_command(self.run_cmd, timeout_seconds)

    def dev(self, timeout_seconds: int = 30) -> ProjectRunOutput:
        return self._execute_command(self.dev_run_cmd, timeout_seconds)

    def test(self, timeout_seconds: int = 30) -> ProjectRunOutput:
        def process_test_metrics(cmd_out: CommandRunOutput, run_out: ProjectRunOutput):
            run_out.test_coverage = self._get_coverage_from_stdout(cmd_out.stdout)
            run_out.test_failed = self._compress_test_failures(self.framework, cmd_out.stdout)

        return self._execute_command(self.test_cmd, timeout_seconds, post_processor=process_test_metrics)

    # --- Helper Parsing Extraction Methods ---

    @staticmethod
    def _get_coverage_from_stdout(stdout: str | None) -> int | None:
        if not stdout:
            return None
        # Example matcher for: All files | 87.5 | 90 | 94.12
        match = re.search(r"All files\s+\|\s+([\d.]+)\s+\|\s+([\d.]+)\s+\|\s+([\d.]+)", stdout)
        if match:
            try:
                return int(float(match.group(1)))
            except ValueError:
                return None
        return None

    @staticmethod
    def _compress_test_failures(framework: Framework, stdout: str | None) -> str | None:
        if not stdout:
            return None
        identifiers = FrameworkIdentifiers.getIdentifiers(framework)
        if not identifiers:
            return None
        
        # Scans lines to filter out framework errors while eliminating noise rows
        failed_lines = []
        for line in stdout.splitlines():
            if any(sig in line for sig in identifiers.fail_sigs) or any(ind in line for ind in identifiers.err_indicators):
                if not any(noise in line for noise in identifiers.noise):
                    failed_lines.append(line.strip())
                    
        return "\n".join(failed_lines) if failed_lines else None
