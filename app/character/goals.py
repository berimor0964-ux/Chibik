from dataclasses import dataclass
from enum import Enum


class GoalType(Enum):
    EAT = "eat"
    SLEEP = "sleep"
    HAVE_FUN = "have_fun"
    SOCIALIZE = "socialize"
    WASH = "wash"
    RELAX = "relax"
    EXPLORE = "explore"
    BUILD = "build"
    TALK = "talk"


@dataclass
class Goal:
    type: GoalType
    priority: float = 50.0
    target_id: str | None = None
    description: str = ""
    completed: bool = False