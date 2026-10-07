from dataclasses import dataclass, field
from typing import Any

from app.character.character import Character
from app.character.memory import Memory


@dataclass
class AIContext:

    character: Character

    user_message: str | None = None

    memories: list[Memory] = field(
        default_factory=list
    )

    world_data: dict[str, Any] = field(
        default_factory=dict
    )

    system_data: dict[str, Any] = field(
        default_factory=dict
    )

    conversation_history: list[
        dict[str, str]
    ] = field(
        default_factory=list
    )

    # =========================================================
    # MEMORY
    # =========================================================

    def add_memory(
        self,
        memory: Memory
    ) -> None:

        self.memories.append(
            memory
        )

    def add_world_data(
        self,
        key: str,
        value: Any
    ) -> None:

        self.world_data[key] = value

    def add_system_data(
        self,
        key: str,
        value: Any
    ) -> None:

        self.system_data[key] = value

    # =========================================================
    # CONVERSATION
    # =========================================================

    def add_message(
        self,
        role: str,
        content: str
    ) -> None:

        self.conversation_history.append({
            "role": role,
            "content": content
        })

    # =========================================================
    # CHARACTER
    # =========================================================

    def build_character_context(self) -> str:

        character = self.character

        personality = (
            character
            .personality
            .build_description()
        )

        return f"""
Имя персонажа: {character.name}

Возраст: {character.age}

Характер:
{personality}

Текущее состояние:
{character.state}

Потребности:
{character.needs}
""".strip()

    # =========================================================
    # MEMORY
    # =========================================================

    def build_memory_context(self) -> str:

        if not self.memories:
            return "Память отсутствует."

        return "\n".join(
            f"- {memory.content}"
            for memory in self.memories
        )

    # =========================================================
    # CONVERSATION
    # =========================================================

    def build_conversation_context(self) -> str:

        if not self.conversation_history:

            return (
                "История текущего "
                "диалога отсутствует."
            )

        return "\n".join(
            f"{message['role']}: "
            f"{message['content']}"
            for message
            in self.conversation_history
        )