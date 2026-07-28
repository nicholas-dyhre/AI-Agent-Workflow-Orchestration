import subprocess
from typing import Dict
from Tasks.Task import CodeChange, Task


def get_diff_for_most_recent_commit(self, task: Task) -> str:
    new_commit = CodeChange[-1].commit_hash
    old_commit = CodeChange[-2].commit_hash
    return self.get_diff_between_commits(old_commit, new_commit).diff


def get_diff_between_commits(self, old_commit: str, new_commit: str) -> Dict[str, str]:
    result = subprocess.run(
        ["git", "diff", old_commit, new_commit], capture_output=True, text=True, check=True
    )

    return {"old_commit": old_commit, "new_commit": new_commit, "diff": result.stdout.strip()}
