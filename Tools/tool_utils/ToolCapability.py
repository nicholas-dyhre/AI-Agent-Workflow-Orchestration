from enum import Enum

class ToolCapability(str, Enum):
    READ_FILES = "read_files"
    WRITE_FILES = "write_files" # Write code

    READ_TASKS = "read_tasks" # Default
    SAVE_TASKS = "save_tasks"
    UPDATE_TASKS = "update_tasks" # Default
    MODIFY_TASKS = "modify_tasks"
    WRITE_TASK_LOGS = "write_task_logs"
    CREATE_TASK = "create_task"
    CREATE_PLAN_STEP = "create_plan_step"

    EXECUTE_COMMANDS = "execute_commands"
    GENERATE_CODE = "generate_code"
    CODE = "code"
    CREATE_BRANCH = "create_branch"
    CREATE_PULL_REQUEST = "create_pull_request"
    CREATE_REPOSITORY = "create_repository"
    GET_CODE_CHANGES = "get_code_changes"
    RUN_TESTS = "run_tests"
    COMMIT_CHANGES = "commit_changes"
    GIT = "git"
    READ_PLAN_STEPS = "read_plan_steps"
    PUSH_CHANGES = "push_changes"
    GIT_GET_REPO_INFO = "git_get_repo_info"

    RESTRCITED_UNTIL_FURTHER_CLARIFICATION = "restricted"

    LOAD_SKILL = "load_skill" # Default

