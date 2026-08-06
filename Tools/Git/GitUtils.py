import logging
import re
import subprocess
from pathlib import Path
from typing import ClassVar, Optional

logger = logging.getLogger(__name__)

class GitUtils:
    _repo_base_path: ClassVar[Optional[Path]] = None

    @classmethod
    def set_repo_path(cls, path: str | Path) -> None:
        cls._repo_base_path = Path(path).resolve()

    @classmethod
    def _get_configured_path(cls) -> Path:
        if cls._repo_base_path is None:
            raise ValueError("GitUtils base path configuration targets are unset.")
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
    def _run_git_cmd(cls, args: list[str]) -> tuple[int, str]:
        """Helper to safely execute git commands inside the repository environment."""
        base = cls._get_configured_path()
        try:
            res = subprocess.run(
                ["git"] + args,
                cwd=base,
                text=True,
                capture_output=True,
                timeout=10
            )
            return res.returncode, res.stdout if res.returncode == 0 else res.stderr
        except Exception as e:
            return -1, str(e)

    @classmethod
    def is_repository(cls) -> bool:
        """Returns True if the runtime directory targets are tracked by active git structures."""
        code, _ = cls._run_git_cmd(["rev-parse", "--is-inside-work-tree"])
        return code == 0

    @classmethod
    def create_repository(cls) -> str:
        """Initializes an entirely clean Git tracking instance locally inside target workspace pathing."""
        cls._create_git_ignore_file()
        if cls.is_repository():
            return "Notice: Target path workspace is already actively tracked by a Git configuration repository."
        code, out = cls._run_git_cmd(["init"])
        if code == 0:
            cls._run_git_cmd(["checkout", "-b", "main"])
            return "Success: Safely initialized target directory as new local Git repository on branch 'main'."
        return f"Error establishing tracking repository engine: {out}"

    @classmethod
    def _create_git_ignore_file(cls) -> None:
        base = cls._safe_resolve(".gitignore")
        if base.is_file():
            return
        
        gitignore_content = (
            "__pycache__/\n"
            "*.py[cod]\n"
            "*$py.class\n"
            ".env\n"
            "venv/\n"
            ".venv/\n"
            ".vscode/\n"
            ".idea/\n"
            "Tasks/\n"
        )
        
        try:
            with open(base, "w", encoding="utf-8") as f:
                f.write(gitignore_content)
            
            cls._run_git_cmd(["add", ".gitignore"])
        except IOError as e:
            raise Exception(f"Failed to create '.gitignore': {str(e)}")

    @classmethod
    def get_current_branch(cls) -> str:
        """Identifies active checked out head path pointers inside operational repositories."""
        code, out = cls._run_git_cmd(["branch", "--show-current"])
        return out.strip() if code == 0 else f"Error parsing current checkout: {out.strip()}"

    @classmethod
    def get_latest_commit(cls) -> str:
        """Fetches the immediate terminal history log signature summarizing target workspace HEAD tracking status."""
        code, out = cls._run_git_cmd(["log", "-1", "--oneline"])
        if code != 0:
            return "Notice: No commit transactions found yet inside local tracking repository registers."
        return f"HEAD Commit Signature: {out.strip()}"

    @classmethod
    def create_branch(cls, branch_name: str) -> str:
        """Deploys a distinct isolated state pointer and switches the working environment over cleanly."""
        sanitized_name = branch_name.replace(" ", "-").replace("'", "")
        code, out = cls._run_git_cmd(["checkout", "-b", sanitized_name])
        return f"Success: Switched to workspace feature branch branch context: '{sanitized_name}'." if code == 0 else f"Failed branch branch configuration: {out.strip()}"

    @classmethod
    def commit_changes(cls, message: str) -> str:
        """Gathers workspace modifications, tracking structural edits, and records transactional states."""
        if not message.strip():
            return "Error: Cannot commit changes using blank string summary descriptors."
        
        cls._run_git_cmd(["add", "."])
        
        status_code, status_out = cls._run_git_cmd(["status", "--porcelain"])
        if not status_out.strip():
            return "Notice: Workspace clean. No outstanding modifications require transaction recording."

        code, out = cls._run_git_cmd(["commit", "-m", message])
        return f"Success: Tracked modifications committed safely.\n{out.strip()}" if code == 0 else f"Commit validation transaction failed: {out.strip()}"

    @classmethod
    def push_changes(cls, remote_name: str = "origin") -> str:
        """Pushes working milestones upstream to the shared repository cluster."""
        current_branch = cls.get_current_branch()
        code, out = cls._run_git_cmd(["push", remote_name, current_branch, "--set-upstream"])
        return f"Success: Safely synchronized working state milestones to remote: {remote_name}/{current_branch}." if code == 0 else f"Remote tracking synchronize transaction failed: {out.strip()}"

    @classmethod
    def create_pull_request(cls, title: str, body: str, draft: bool = False) -> tuple[bool, str]:
        """
        Creates a GitHub Pull Request using the local 'gh' CLI tool.
        Automatically handles spaces and quotes inside the title and body safely.
        """
        if not cls.is_repository():
            return False, "Error: Cannot create a pull request outside of a valid Git repository."

        current_branch = cls.get_current_branch()
        if current_branch in ["main", "master", "HEAD", ""]:
            return False, f"Error: Cannot create a pull request directly from protected branch '{current_branch}'."

        args = [
            "gh", "pr", "create",
            "--title", title,
            "--body", body,
            "--assignee", "@me"
        ]

        if draft:
            args.append("--draft")

        try:
            returncode, output_msg = cls._run_git_cmd(args)
            
            if returncode != 0:
                if "no upstream configured" in output_msg.lower():
                    return False, "Error: Upstream target missing. You must call GitUtils.push_changes() before creating a PR."
                return False, f"Error creating Pull Request: {output_msg.strip()}"
                
            return True, f"Success: Pull Request opened successfully.\n{output_msg.strip()}"
            
        except Exception as e:
            return False, f"Critical error executing Pull Request pipeline: {str(e)}"

    @classmethod
    def get_diff(cls, sub_path: Optional[str] = None, depth: int = 3) -> str:
        """Returns uncommitted modifications (working directory changes vs HEAD)."""
        args = ["diff", "HEAD" f"-U{depth}"]
        if sub_path:
            try:
                args.append(str(cls._safe_resolve(sub_path)))
            except Exception as e:
                return str(e)
                
        code, output = cls._run_git_cmd(args)
        return output if output.strip() else "No uncommitted modifications detected."

    @classmethod
    def is_diff_empty(cls, sub_path: Optional[str] = None) -> bool | str:
        """Returns uncommitted modifications (working directory changes vs HEAD)."""
        output = cls.get_diff(sub_path)
        success = False if "No uncommitted" in output else True
        return success
        
    @classmethod
    def get_rich_contextual_diff(cls) -> str:
        """
        Generates clean GitHub-style contextual blocks for reviewing changes.
        Limits visual drift to absolute token minimums using standard diff bounds.
        """
        try:
            stdout_data = cls.get_diff()
                
            if not stdout_data.strip():
                return "Workspace status clean. No modified code assets found relative to HEAD repository snapshot."
            
            formatted_diff = []
            current_file = ""
            
            for line in stdout_data.splitlines():
                if line.startswith("diff --git"):
                    match = re.search(r"b/(.*)$", line)
                    current_file = match.group(1) if match else "unknown"
                    formatted_diff.append(f"\n📁 FILE MODIFIED: {current_file}\n---")
                elif line.startswith("@@"):
                    formatted_diff.append(f"  Scope context {line}")
                elif line.startswith("+") and not line.startswith("+++"):
                    formatted_diff.append(f"    [ADDED]   {line[1:]}")
                elif line.startswith("-") and not line.startswith("---"):
                    formatted_diff.append(f"    [REMOVED] {line[1:]}")
                elif line.startswith(" "):
                    formatted_diff.append(f"    [ANCHOR]  {line[1:]}")
                    
            return "\n".join(formatted_diff)[:2500]
            
        except Exception as e:
            return f"Critical exception collecting contextual repo changes: {str(e)}"

    @classmethod
    def checkout_branch(cls, branch_name: str, create_if_missing: bool = False) -> tuple[bool, str]:
        """
        Switches the repository context to a different branch.
        Can optionally create and track the branch if it does not exist.
        """
        if not cls.is_repository():
            return False, "Error: Cannot switch branches outside of a valid Git repository."

        sanitized_name = branch_name.strip().replace(" ", "-")
        if not sanitized_name:
            return False, "Error: Branch name cannot be empty."
        
        args = ["checkout"]
        if create_if_missing:
            args.append("-b")
        args.append(sanitized_name)

        try:
            returncode, output_msg = cls._run_git_cmd(args)
            
            if returncode != 0:
                if "pathspec" in output_msg.lower() and not create_if_missing:
                    return False, (
                        f"Error: Branch '{sanitized_name}' does not exist locally. "
                        "Set 'create_if_missing=True' if you intend to create a new branch."
                    )
                return False, f"Error switching to branch '{sanitized_name}': {output_msg.strip()}"

            print(f"Switched working repository context to branch: '{sanitized_name}'.")
            return True, sanitized_name
            
        except Exception as e:
            return False, f"Critical error executing branch checkout pipeline: {str(e)}"

    @classmethod
    def branch_exists(cls, branch_name: str) -> bool:
        """
        Checks if a branch with the specified name exists either locally 
        or as a tracked remote branch. Returns True if found, otherwise False.
        """
        if not cls.is_repository():
            return False

        sanitized_name = branch_name.strip().replace(" ", "-")
        if not sanitized_name:
            return False

        returncode, output_msg = cls._run_git_cmd(["show-ref", "--verify", f"refs/heads/{sanitized_name}"])
        if returncode == 0:
            return True

        returncode, output_msg = cls._run_git_cmd(["branch", "-a", "--list", f"*{sanitized_name}"])
        if returncode == 0 and sanitized_name in output_msg:
            return True

        return False

    @classmethod
    def get_repo_status(cls) -> tuple[bool, str]:
        """Returns untracked, modified, and staged file summaries."""
        code, output = cls._run_git_cmd(["status", "--short"])
        return (True, output) if output.strip() else (False, "Repository is completely clean.")