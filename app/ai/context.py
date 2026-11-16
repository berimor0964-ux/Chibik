"""Контекст для LLM: собирает информацию о персонаже, памяти и мире."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.character.character import Character
from app.character.memory import Memory


@dataclass
class AIContext:
    """Собирает всю информацию, которую LLM использует для генерации ответа."""

    character: Character
    user_message: str = ""
    memories: list[Memory] = field(default_factory=list)
    world_data: dict[str, Any] = field(default_factory=dict)
    system_data: dict[str, Any] = field(default_factory=dict)
    conversation_history: list[dict[str, str]] = field(default_factory=list)

    # === ДОБАВЛЕНО: метод для добавления системных данных ===
    def add_system_data(self, data: dict[str, Any]) -> None:
        """Добавляет системные данные в контекст."""
        self.system_data.update(data)

    def build_character_context(self) -> str:
        """Формирует описание персонажа для промпта."""
        parts = []
        parts.append(f"Имя: {self.character.name}")
        parts.append(f"Возраст: {self.character.age}")

        needs = self.character.needs
        parts.append(f"Энергия: {needs.energy:.0f}%")
        parts.append(f"Голод: {needs.hunger:.0f}%")
        parts.append(f"Веселье: {needs.fun:.0f}%")
        parts.append(f"Общение: {needs.social:.0f}%")
        parts.append(f"Гигиена: {needs.hygiene:.0f}%")
        parts.append(f"Комфорт: {needs.comfort:.0f}%")

        if hasattr(self.character.state, "mood"):
            parts.append(f"Настроение: {self.character.state.mood}")

        personality = self.character.personality
        if personality.backstory:
            parts.append(f"Предыстория: {personality.backstory}")
        if hasattr(personality, "behavior_style") and personality.behavior_style:
            parts.append(f"Манера поведения: {personality.behavior_style}")
        if personality.traits:
            parts.append(f"Черты характера: {', '.join(personality.traits)}")

        return "\n".join(parts)

    def build_memory_context(self) -> str:
        """Тянет память из БД, если sync подключён."""
        if hasattr(self.character, "db_sync") and self.character.db_sync:
            return self.character.db_sync.build_memory_context(limit=8)

        memories = self.character.memory.get_recent(limit=8)
        if not memories:
            return ""
        lines = [f"- [{m.memory_type.value}] {m.content}" for m in memories]
        return "\n".join(lines)

    def build_conversation_context(self) -> str:
        """История последних сообщений."""
        if self.conversation_history:
            lines = []
            for msg in self.conversation_history[-10:]:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "user":
                    lines.append(f"- Вы: {content}")
                else:
                    lines.append(f"- {self.character.name}: {content}")
            return "\n".join(lines)

        if not self.memories:
            return ""
        dialog_memories = [
            m for m in self.memories
            if m.metadata.get("type") == "conversation"
        ][:10]
        if not dialog_memories:
            return ""
        return "\n".join(f"- {m.content}" for m in dialog_memories)

    def build_world_context(self) -> str:
        """Информация о мире."""
        if not self.world_data:
            return ""
        parts = []
        if "room" in self.world_data:
            parts.append(f"Комната: {self.world_data['room']}")
        if "objects" in self.world_data:
            parts.append(f"Предметы: {', '.join(self.world_data['objects'])}")
        if "position" in self.world_data:
            pos = self.world_data["position"]
            parts.append(f"Позиция: x={pos[0]:.1f}, y={pos[1]:.1f}")
        return "\n".join(parts)

    def build_system_context(self) -> str:
        """Системные данные (если есть)."""
        if not self.system_data:
            return ""
        parts = []
        for key, value in self.system_data.items():
            parts.append(f"{key}: {value}")
        return "\n".join(parts)

    def build_full_prompt(self) -> str:
        """Собирает полный контекст для LLM."""
        sections = []
        sections.append("=== ПЕРСОНАЖ ===")
        sections.append(self.build_character_context())
        sections.append("\n=== ПАМЯТЬ ===")
        sections.append(self.build_memory_context() or "Воспоминаний пока нет.")
        sections.append("\n=== ИСТОРИЯ ДИАЛОГА ===")
        sections.append(self.build_conversation_context() or "Это первое сообщение.")
        sections.append("\n=== МИР ===")
        sections.append(self.build_world_context() or "Информация о мире недоступна.")

        # Добавляем системные данные, если есть
        system_ctx = self.build_system_context()
        if system_ctx:
            sections.append("\n=== СИСТЕМНЫЕ ДАННЫЕ ===")
            sections.append(system_ctx)

        sections.append("\n=== СООБЩЕНИЕ ПОЛЬЗОВАТЕЛЯ ===")
        sections.append(self.user_message)
        return "\n".join(sections)