from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class MemoryType(Enum):
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    EPISODIC = "episodic"


@dataclass
class Memory:
    content: str

    memory_type: MemoryType

    importance: float = 50.0

    created_at: datetime = field(
        default_factory=datetime.now
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


@dataclass
class MemoryStore:

    memories: list[Memory] = field(
        default_factory=list
    )

    # =========================================================
    # REMEMBER
    # =========================================================

    def remember(
        self,
        content: str,
        memory_type: MemoryType = MemoryType.SHORT_TERM,
        importance: float = 50.0,
        metadata: dict[str, Any] | None = None
    ) -> Memory:

        importance = max(
            0.0,
            min(
                importance,
                100.0
            )
        )

        memory = Memory(
            content=content,
            memory_type=memory_type,
            importance=importance,
            metadata=metadata or {}
        )

        self.memories.append(
            memory
        )

        return memory

    # =========================================================
    # INTERACTION
    # =========================================================

    def remember_interaction(
        self,
        user_message: str,
        assistant_message: str
    ) -> Memory:

        return self.remember(
            content=(
                f"Пользователь: "
                f"{user_message}\n"
                f"Персонаж: "
                f"{assistant_message}"
            ),
            memory_type=MemoryType.EPISODIC,
            importance=40.0,
            metadata={
                "type": "conversation"
            }
        )

    # =========================================================
    # USER FACT
    # =========================================================

    def remember_user_fact(
        self,
        fact: str,
        importance: float = 80.0
    ) -> Memory:

        return self.remember(
            content=fact,
            memory_type=MemoryType.LONG_TERM,
            importance=importance,
            metadata={
                "type": "user_fact"
            }
        )

    # =========================================================
    # SEARCH
    # =========================================================

    def search(
        self,
        query: str
    ) -> list[Memory]:

        query = query.lower()

        return [
            memory
            for memory in self.memories
            if query in memory.content.lower()
        ]

    # =========================================================
    # BY TYPE
    # =========================================================

    def get_by_type(
        self,
        memory_type: MemoryType
    ) -> list[Memory]:

        return [
            memory
            for memory in self.memories
            if memory.memory_type == memory_type
        ]

    # =========================================================
    # IMPORTANT MEMORIES
    # =========================================================

    def get_important(
        self,
        minimum_importance: float = 70.0
    ) -> list[Memory]:

        return [
            memory
            for memory in self.memories
            if memory.importance >= minimum_importance
        ]

    # =========================================================
    # RECENT
    # =========================================================

    def get_recent(
        self,
        limit: int = 20
    ) -> list[Memory]:

        return self.memories[-limit:]

    # =========================================================
    # REMOVE
    # =========================================================

    def remove(
        self,
        memory: Memory
    ) -> None:

        if memory in self.memories:
            self.memories.remove(
                memory
            )

    # =========================================================
    # SHORT TERM CLEANUP
    # =========================================================

    def clear_short_term(self) -> None:

        self.memories = [
            memory
            for memory in self.memories
            if memory.memory_type
            != MemoryType.SHORT_TERM
        ]