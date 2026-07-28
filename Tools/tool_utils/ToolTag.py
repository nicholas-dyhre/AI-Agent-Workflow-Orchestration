from enum import Enum

class ToolTag(str, Enum):
    TASKS = "tasks" # Default
    PERSISTENCE = "persistence"
    FILESYSTEM = "filesystem"
    LOGGING = "logging"
    QUERY = "query"
    VALIDATION = "validation"
    SKILLS = "skills" # Default
    UTILITY = "utility" # Default
    DEVELOPMENT = "development"
    TESTING = "testing"
    GENERATION = "generation"
    GIT = "git"