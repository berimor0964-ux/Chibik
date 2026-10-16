from dataclasses import dataclass

@dataclass
class CharacterState:
    x: float = 0.0
    y: float = 0.0

    current_action: str = "idle"
    mood: str = "neutral"

