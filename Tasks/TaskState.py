from enum import Enum


# class syntax
class State(Enum):
    CREATED = "created"
    READY_FOR_PLANNING = "ready_for_planning"
    PLANNING = "planning"
    READY_FOR_DEVELOPMENT = "ready_for_development"
    DEVELOPMENT = "development"
    READY_FOR_REVIEW = "ready_for_review"
    REVIEW = "review"
    READY_FOR_MERGE = "ready_for_merge"  # This step isdone by a human
    MERGED = "merged"  # The final state after merging, no more actions needed

    @classmethod
    def pending_states(cls) -> set["State"]:
        return {
            cls.CREATED,
            cls.READY_FOR_PLANNING,
        }

    @classmethod
    def completed_states(cls) -> set["State"]:
        return {
            cls.READY_FOR_MERGE,
            cls.MERGED,
        }

    @classmethod
    def ready_states(cls) -> set["State"]:
        return {
            cls.READY_FOR_PLANNING,
            cls.READY_FOR_DEVELOPMENT,
            cls.READY_FOR_REVIEW,
        }

    @classmethod
    def active_states(cls) -> set["State"]:
        return {
            cls.PLANNING,
            cls.DEVELOPMENT,
            cls.REVIEW,
        }
