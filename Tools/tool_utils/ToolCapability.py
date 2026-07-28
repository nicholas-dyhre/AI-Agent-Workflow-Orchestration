from enum import Enum

class ToolCapability(str, Enum):
    READ_FILES = "read_files"
    WRITE_FILES = "write_files" # Write code

    READ_TASKS = "read_tasks" # Default
    SAVE_TASKS = "save_tasks"
    UPDATE_TASKS = "update_tasks" # Default
    MODIFY_TASKS = "modify_tasks"
    VALIDATE_TASKS = "validate_tasks" # Default
    WRITE_TASK_LOGS = "write_task_logs"
    CREATE_TASK = "create_task"

    EXECUTE_COMMANDS = "execute_commands"
    GENERATE_CODE = "generate_code"
    CREATE_BRANCH = "create_branch"
    CREATE_PULL_REQUEST = "create_pull_request"
    GET_CODE_CHANGES = "get_code_changes"
    RUN_TESTS = "run_tests" # TODO: Create tool for this
 

    LOAD_SKILL = "load_skill" # Default