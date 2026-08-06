from dataclasses import dataclass
from fnmatch import fnmatch
import os
from pathlib import Path
from typing import ClassVar
from enum import Enum


class Framework(Enum):
    Java = "Java"
    Dotnet = "Dotnet"
    Javascript = "Javascript"
    Python = "Python"
    Go = "Go"

@dataclass
class TestIdentifier:
    fail_sigs: list[str]
    err_indicators: list[str]
    noise: list[str]


class FrameworkIdentifiers():
    frameworks: ClassVar[dict[Framework, TestIdentifier]] = {
        Framework.Python: TestIdentifier(
            fail_sigs=["FAIL:", "ERROR:", "E "],
            err_indicators=["AssertionError:", "E"],
            noise = ["Traceback", "File \"", "platform ", "plugins:"]
        ),
        Framework.Dotnet: TestIdentifier(
            fail_sigs = ["Failed", "Error:"],
            err_indicators = ["Expected:", "Actual:", "Error Message:", "Stack Trace:"],
            noise = ["Total tests:", "Passed:", "Failed:"]
        ),
        Framework.Go: TestIdentifier(
            fail_sigs = ["--- FAIL:"],
            err_indicators = ["Error:", "panic:", "want", "got"],
            noise = ["=== RUN", "testing.go:"]
        ),
        Framework.Java: TestIdentifier(
            fail_sigs = ["Failure", "Error", "::"],
            err_indicators = ["Exception in thread", "expected:<", "actual:<", "at "],
            noise = ["Running ", "Tests run:"]
        ),
        Framework.Javascript: TestIdentifier(
            fail_sigs = ["●", "❌", "FAIL "],
            err_indicators = ["Error:", "expect(", "at "],
            noise = ["Test Suites:", "Snapshots:", "Time:"]
        ),
    }

    file_indicators: ClassVar[dict[Framework, list[str]]] = {
        Framework.Python: [
            "requirements.txt",
            "pyproject.toml",
            "*.py",
        ],
        Framework.Javascript: [
            "package.json"
        ],
        Framework.Dotnet: [
            "*.csproj"
        ],
        Framework.Go: [],
        Framework.Java: [],
    }

    @classmethod
    def getIdentifiers(cls, frameworkIdentifier: Framework) -> TestIdentifier | None:
        return cls.frameworks.get(frameworkIdentifier, None)


    @staticmethod
    def getFrameworkFromFileIndicator(target: Path) -> Framework | None:
        exact_matches: dict[str, Framework] = {}
        wildcard_matches: list[tuple[str, Framework]] = []

        for framework, patterns in FrameworkIdentifiers.file_indicators.items():
            for pattern in patterns:
                if "*" in pattern:
                    wildcard_matches.append((pattern, framework))
                else:
                    exact_matches[pattern] = framework

        for _, _, filenames in os.walk(target):
            for file_name in filenames:
                if file_name in exact_matches:
                    return exact_matches[file_name]
                
                for pattern, framework in wildcard_matches:
                    if fnmatch(file_name, pattern):
                        return framework
                        
        return None


        