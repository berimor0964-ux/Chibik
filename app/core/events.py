#Заглушка событий EventBus.

from dataclasses import dataclass


# ---- События от World (№1) ----
@dataclass
class CharacterMoved:
    character_id: str
    x: float
    y: float


@dataclass
class ObjectCreated:
    object_id: str
    type: str
    x: float
    y: float


@dataclass
class ObjectRemoved:
    object_id: str


@dataclass
class BuildingCreated:
    building_id: str
    type: str
    x: float
    y: float


# ---- События от Character (№2) ----
@dataclass
class CharacterChangedState:
    character_id: str
    state: str   # IDLE / WALK / SLEEP / EAT / ...


@dataclass
class CharacterSpoke:
    character_id: str
    text: str


@dataclass
class NeedChanged:
    character_id: str
    need: str          # hunger / energy / fun / ...
    value: float       # 0.0 .. 100.0


# ---- События от System (№4) ----
@dataclass
class NotificationCreated:
    title: str
    text: str
    icon: str = ""


@dataclass
class VoiceInputReceived:
    text: str


@dataclass
class FileSearchCompleted:
    query: str
    results: list[str]