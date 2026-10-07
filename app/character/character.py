from dataclasses import dataclass, field
from uuid import uuid4

from .state import CharacterState
from .needs import Needs
from .personality import Personality
from .relationships import Relationships
from .memory import MemoryStore


@dataclass
class Character:
    name: str
    age: int

    id: str = field(
        default_factory=lambda: str(uuid4())
    )

    state: CharacterState = field(
        default_factory=CharacterState
    )

    needs: Needs = field(
        default_factory=Needs
    )

    personality: Personality = field(
        default_factory=Personality
    )

    relationships: Relationships = field(
        default_factory=Relationships
    )

    memory: MemoryStore = field(
        default_factory=MemoryStore
    )

    def get_state(self) -> CharacterState:
        return self.state

    def get_needs(self) -> Needs:
        return self.needs

    def set_goal(self, goal) -> None:
        self.state.current_action = goal.type.value

    def perform_action(self, action) -> None:
        self.state.current_action = action.type.value

    def get_personality_description(self) -> str:
        return self.personality.build_description()