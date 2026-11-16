"""Мост между EventBus / LLM-контекстом и Database."""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from app.core import events as ev
from app.core.event_bus import EventBus
from app.database.database import Database


class DatabaseSync:
    """Подписывается на события и пишет их в базу; читает память для LLM."""

    def __init__(self, db: Database, bus: EventBus, character_id: str):
        self.db = db
        self.bus = bus
        self.character_id = character_id
        self.db.set_active_character(character_id)
        self._subscriptions: list[tuple[type, Any]] = []

    # ---------- запись событий ----------

    def attach(self) -> None:
        handlers = {
            ev.CharacterMoved: self._on_moved,
            ev.CharacterSpoke: self._on_spoke,
            ev.MemoryCreated: self._on_memory,
            ev.NeedChanged: self._on_need,
            ev.ObjectCreated: self._on_object,
            ev.BuildingCreated: self._on_building,
            ev.NotificationCreated: self._on_notification,
            ev.VoiceInputReceived: self._on_voice,
            ev.FileSearchCompleted: self._on_filesearch,
        }
        for event_type, handler in handlers.items():
            self.bus.subscribe(event_type, handler)
            self._subscriptions.append((event_type, handler))

    def detach(self) -> None:
        for event_type, handler in self._subscriptions:
            self.bus.unsubscribe(event_type, handler)
        self._subscriptions.clear()

    def _on_moved(self, e: ev.CharacterMoved) -> None:
        self.db.log_event("CharacterMoved", {"x": e.x, "y": e.y}, self.character_id)

    def _on_spoke(self, e: ev.CharacterSpoke) -> None:
        self.db.log_event("CharacterSpoke", {"text": e.text}, self.character_id)

    def _on_memory(self, e: ev.MemoryCreated) -> None:
        self.db.log_event("MemoryCreated", {"content": e.content}, self.character_id)

    def _on_need(self, e: ev.NeedChanged) -> None:
        self.db.log_event("NeedChanged", {"need": e.need, "value": e.value}, self.character_id)

    def _on_object(self, e: ev.ObjectCreated) -> None:
        self.db.log_event("ObjectCreated", {"name": e.name, "x": e.x, "y": e.y})

    def _on_building(self, e: ev.BuildingCreated) -> None:
        self.db.log_event("BuildingCreated", {"name": e.name})

    def _on_notification(self, e: ev.NotificationCreated) -> None:
        self.db.log_event("NotificationCreated", {"text": e.text})

    def _on_voice(self, e: ev.VoiceInputReceived) -> None:
        self.db.log_event("VoiceInput", {"text": e.text})

    def _on_filesearch(self, e: ev.FileSearchCompleted) -> None:
        self.db.log_event("FileSearch", {"query": e.query, "count": len(e.results)})

    # ---------- чтение для LLM ----------

    def build_memory_context(self, limit: int = 8) -> str:
        """Топ-N воспоминаний для подстановки в промпт."""
        memories = self.db.load_memories(self.character_id, limit=200)
        # сортировка: сначала по важности, потом по свежести
        memories.sort(key=lambda m: (m.importance, m.created_at), reverse=True)
        top = memories[:limit]
        if not top:
            return ""
        lines = [f"- [{m.memory_type.value}] {m.content}" for m in top]
        return "\n".join(lines)

    def build_relationship_context(self) -> str:
        rels = self.db.load_relationships(self.character_id)
        if not rels:
            return ""
        lines = [
            f"- {r['other_name']}: дружба={r['friendship']:.0f}, "
            f"доверие={r['trust']:.0f}, уважение={r['respect']:.0f}"
            for r in rels
        ]
        return "\n".join(lines)

    def build_goals_context(self) -> str:
        goals = self.db.active_goals(self.character_id)
        if not goals:
            return ""
        return "\n".join(f"- {g['type']} (приоритет {g['priority']:.0f}): {g['description']}"
                         for g in goals)