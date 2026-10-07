from dataclasses import dataclass
from enum import Enum


class ActionType(Enum):
    IDLE = "idle"
    MOVE = "move"
    EAT = "eat"
    SLEEP = "sleep"
    PLAY = "play"
    TALK = "talk"
    WASH = "wash"
    RELAX = "relax"
    EXPLORE = "explore"
    BUILD = "build"


@dataclass
class Action:
    type: ActionType
    target_id: str | None = None
    duration: float = 0.0
    completed: bool = False