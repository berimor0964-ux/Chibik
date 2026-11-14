
from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from app.character.memory import Memory, MemoryType


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = PROJECT_ROOT / "desktop_pet.db"


class Database:
    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.active_character_id: str | None = None
        self._create_tables()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _create_tables(self) -> None:
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    character_id TEXT NOT NULL,
                    user_message TEXT NOT NULL,
                    assistant_message TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    character_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    memory_type TEXT NOT NULL,
                    importance REAL NOT NULL DEFAULT 50,
                    created_at TEXT NOT NULL,
                    metadata TEXT NOT NULL DEFAULT '{}'
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_interactions_character
                ON interactions(character_id, id)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_memories_character
                ON memories(character_id, id)
            """)

    def set_active_character(self, character_id: str) -> None:
        self.active_character_id = str(character_id)

    def _character_id(self, character_id: str | None = None) -> str:
        result = character_id or self.active_character_id
        if not result:
            raise ValueError(
                "Не выбран персонаж. Сначала вызови "
                "database.set_active_character(character.id)."
            )
        return str(result)

    def save_interaction(
        self,
        user_message: str,
        assistant_message: str,
    ) -> None:
        character_id = self._character_id()

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO interactions (
                    character_id,
                    user_message,
                    assistant_message,
                    created_at
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    character_id,
                    user_message,
                    assistant_message,
                    datetime.now().isoformat(),
                ),
            )

    def load_interactions(
        self,
        character_id: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, str]]:
        character_id = self._character_id(character_id)
        limit = max(1, min(int(limit), 500))

        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT user_message, assistant_message
                FROM (
                    SELECT id, user_message, assistant_message
                    FROM interactions
                    WHERE character_id = ?
                    ORDER BY id DESC
                    LIMIT ?
                )
                ORDER BY id ASC
                """,
                (character_id, limit),
            ).fetchall()

        history: list[dict[str, str]] = []

        for row in rows:
            history.append({
                "role": "user",
                "content": row["user_message"],
            })
            history.append({
                "role": "assistant",
                "content": row["assistant_message"],
            })

        return history

    def save_memory(self, memory: Memory) -> None:
        character_id = self._character_id()

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO memories (
                    character_id,
                    content,
                    memory_type,
                    importance,
                    created_at,
                    metadata
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    character_id,
                    memory.content,
                    memory.memory_type.value,
                    memory.importance,
                    memory.created_at.isoformat(),
                    json.dumps(
                        memory.metadata,
                        ensure_ascii=False,
                        default=str,
                    ),
                ),
            )

    def load_memories(
        self,
        character_id: str | None = None,
        limit: int = 500,
    ) -> list[Memory]:
        character_id = self._character_id(character_id)
        limit = max(1, min(int(limit), 5000))

        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT content, memory_type, importance,
                       created_at, metadata
                FROM (
                    SELECT id, content, memory_type, importance,
                           created_at, metadata
                    FROM memories
                    WHERE character_id = ?
                    ORDER BY id DESC
                    LIMIT ?
                )
                ORDER BY id ASC
                """,
                (character_id, limit),
            ).fetchall()

        result: list[Memory] = []

        for row in rows:
            try:
                memory_type = MemoryType(row["memory_type"])
            except ValueError:
                memory_type = MemoryType.SHORT_TERM

            try:
                created_at = datetime.fromisoformat(row["created_at"])
            except (TypeError, ValueError):
                created_at = datetime.now()

            try:
                metadata: dict[str, Any] = json.loads(
                    row["metadata"] or "{}"
                )
            except (TypeError, ValueError):
                metadata = {}

            result.append(
                Memory(
                    content=row["content"],
                    memory_type=memory_type,
                    importance=float(row["importance"]),
                    created_at=created_at,
                    metadata=metadata,
                )
            )

        return result

    def close(self) -> None:
        # Соединения закрываются после каждой операции.
        pass
