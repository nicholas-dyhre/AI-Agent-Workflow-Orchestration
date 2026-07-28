from enum import Enum


# class syntax
class State(Enum):
    CREATED = 0
    READY_FOR_PLANNING = 1
    PLANNING = 2
    READY_FOR_DEVELOPMENT = 3
    DEVELOPMENT = 4
    READY_FOR_REVIEW = 5
    REVIEW = 6
    READY_FOR_MERGE = 7  # This step isdone by a human
    MERGED = 8  # The final state after merging, no more actions needed

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
