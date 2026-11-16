"""Единая база данных Chibik: персонажи, память, диалоги, состояние, события."""
from __future__ import annotations

import json
import sqlite3
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from app.character.memory import Memory, MemoryType

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = PROJECT_ROOT / "desktop_pet.db"

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS characters (
    id            TEXT PRIMARY KEY,
    name          TEXT NOT NULL,
    age           INTEGER NOT NULL DEFAULT 1,
    created_at    TEXT NOT NULL,
    last_seen     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS character_state (
    character_id  TEXT PRIMARY KEY REFERENCES characters(id) ON DELETE CASCADE,
    energy        REAL NOT NULL DEFAULT 100,
    hunger        REAL NOT NULL DEFAULT 100,
    fun           REAL NOT NULL DEFAULT 100,
    social        REAL NOT NULL DEFAULT 100,
    hygiene       REAL NOT NULL DEFAULT 100,
    comfort       REAL NOT NULL DEFAULT 100,
    pos_x         REAL NOT NULL DEFAULT 0,
    pos_y         REAL NOT NULL DEFAULT 0,
    scene_mode    TEXT NOT NULL DEFAULT 'room',
    mood          TEXT NOT NULL DEFAULT 'neutral',
    updated_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS personality (
    character_id  TEXT PRIMARY KEY REFERENCES characters(id) ON DELETE CASCADE,
    friendliness  REAL NOT NULL DEFAULT 0.5,
    curiosity     REAL NOT NULL DEFAULT 0.5,
    laziness      REAL NOT NULL DEFAULT 0.3,
    humor         REAL NOT NULL DEFAULT 0.5,
    chaos         REAL NOT NULL DEFAULT 0.3,
    intelligence  REAL NOT NULL DEFAULT 0.5,
    courage       REAL NOT NULL DEFAULT 0.5,
    backstory     TEXT NOT NULL DEFAULT '',
    style         TEXT NOT NULL DEFAULT '',
    likes         TEXT NOT NULL DEFAULT '[]',
    dislikes      TEXT NOT NULL DEFAULT '[]',
    rules         TEXT NOT NULL DEFAULT '[]',
    updated_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS memories (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id  TEXT NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    content       TEXT NOT NULL,
    memory_type   TEXT NOT NULL DEFAULT 'short_term',
    importance    REAL NOT NULL DEFAULT 50,
    created_at    TEXT NOT NULL,
    metadata      TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_mem_char ON memories(character_id, id);
CREATE INDEX IF NOT EXISTS idx_mem_imp  ON memories(character_id, importance DESC);

CREATE TABLE IF NOT EXISTS interactions (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id      TEXT NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    user_message      TEXT NOT NULL,
    assistant_message TEXT NOT NULL,
    created_at        TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_int_char ON interactions(character_id, id);

CREATE TABLE IF NOT EXISTS relationships (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id  TEXT NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    other_name    TEXT NOT NULL,
    friendship    REAL NOT NULL DEFAULT 0,
    trust         REAL NOT NULL DEFAULT 0,
    respect       REAL NOT NULL DEFAULT 0,
    attachment    REAL NOT NULL DEFAULT 0,
    updated_at    TEXT NOT NULL,
    UNIQUE(character_id, other_name)
);

CREATE TABLE IF NOT EXISTS goals (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id  TEXT NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    type          TEXT NOT NULL,
    priority      REAL NOT NULL DEFAULT 50,
    description   TEXT NOT NULL DEFAULT '',
    status        TEXT NOT NULL DEFAULT 'active',
    created_at    TEXT NOT NULL,
    completed_at  TEXT
);
CREATE INDEX IF NOT EXISTS idx_goal_char ON goals(character_id, status);

CREATE TABLE IF NOT EXISTS events (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id  TEXT,
    event_type    TEXT NOT NULL,
    payload       TEXT NOT NULL DEFAULT '{}',
    created_at    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_ev_time ON events(created_at DESC);

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


class Database:
    """Единый слой доступа к SQLite. Потокобезопасен через короткие соединения."""

    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.active_character_id: str | None = None
        self._init_schema()

    # ---------- инфраструктура ----------

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(SCHEMA)

    def set_active_character(self, character_id: str) -> None:
        self.active_character_id = str(character_id)

    def _cid(self, character_id: str | None = None) -> str:
        result = character_id or self.active_character_id
        if not result:
            raise ValueError("Не выбран персонаж. Вызовите set_active_character().")
        return str(result)

    def close(self) -> None:
        pass  # соединения закрываются через context manager

    # ---------- characters ----------

    def create_character(self, character_id: str, name: str, age: int = 1) -> None:
        now = datetime.now().isoformat()
        with self._connect() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO characters (id, name, age, created_at, last_seen) "
                "VALUES (?, ?, ?, ?, ?)",
                (character_id, name, age, now, now),
            )
            conn.execute(
                "INSERT OR IGNORE INTO character_state (character_id, updated_at) VALUES (?, ?)",
                (character_id, now),
            )
            conn.execute(
                "INSERT OR IGNORE INTO personality (character_id, updated_at) VALUES (?, ?)",
                (character_id, now),
            )

    def list_characters(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, name, age, created_at, last_seen FROM characters ORDER BY last_seen DESC"
            ).fetchall()
        return [dict(r) for r in rows]

    def touch_character(self, character_id: str | None = None) -> None:
        cid = self._cid(character_id)
        with self._connect() as conn:
            conn.execute(
                "UPDATE characters SET last_seen = ? WHERE id = ?",
                (datetime.now().isoformat(), cid),
            )

    # ---------- state ----------

    def save_state(self, state: dict[str, Any], character_id: str | None = None) -> None:
        cid = self._cid(character_id)
        with self._connect() as conn:
            conn.execute(
                """UPDATE character_state SET
                    energy=?, hunger=?, fun=?, social=?, hygiene=?, comfort=?,
                    pos_x=?, pos_y=?, scene_mode=?, mood=?, updated_at=?
                WHERE character_id=?""",
                (
                    float(state.get("energy", 100)), float(state.get("hunger", 100)),
                    float(state.get("fun", 100)), float(state.get("social", 100)),
                    float(state.get("hygiene", 100)), float(state.get("comfort", 100)),
                    float(state.get("pos_x", 0)), float(state.get("pos_y", 0)),
                    str(state.get("scene_mode", "room")), str(state.get("mood", "neutral")),
                    datetime.now().isoformat(), cid,
                ),
            )

    def load_state(self, character_id: str | None = None) -> dict[str, Any] | None:
        cid = self._cid(character_id)
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM character_state WHERE character_id = ?", (cid,)
            ).fetchone()
        return dict(row) if row else None

    # ---------- personality ----------

    def save_personality(self, p: dict[str, Any], character_id: str | None = None) -> None:
        cid = self._cid(character_id)
        with self._connect() as conn:
            conn.execute(
                """UPDATE personality SET
                    friendliness=?, curiosity=?, laziness=?, humor=?, chaos=?,
                    intelligence=?, courage=?, backstory=?, style=?,
                    likes=?, dislikes=?, rules=?, updated_at=?
                WHERE character_id=?""",
                (
                    float(p.get("friendliness", 0.5)), float(p.get("curiosity", 0.5)),
                    float(p.get("laziness", 0.3)), float(p.get("humor", 0.5)),
                    float(p.get("chaos", 0.3)), float(p.get("intelligence", 0.5)),
                    float(p.get("courage", 0.5)), str(p.get("backstory", "")),
                    str(p.get("style", "")),
                    json.dumps(p.get("likes", []), ensure_ascii=False),
                    json.dumps(p.get("dislikes", []), ensure_ascii=False),
                    json.dumps(p.get("rules", []), ensure_ascii=False),
                    datetime.now().isoformat(), cid,
                ),
            )

    def load_personality(self, character_id: str | None = None) -> dict[str, Any] | None:
        cid = self._cid(character_id)
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM personality WHERE character_id = ?", (cid,)
            ).fetchone()
        if not row:
            return None
        d = dict(row)
        for key in ("likes", "dislikes", "rules"):
            try:
                d[key] = json.loads(d.get(key) or "[]")
            except (TypeError, ValueError):
                d[key] = []
        return d

    # ---------- memories ----------

    def save_memory(self, memory: Memory, character_id: str | None = None) -> None:
        cid = self._cid(character_id)
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO memories
                    (character_id, content, memory_type, importance, created_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    cid, memory.content, memory.memory_type.value, memory.importance,
                    memory.created_at.isoformat(),
                    json.dumps(memory.metadata, ensure_ascii=False, default=str),
                ),
            )

    def load_memories(self, character_id: str | None = None, limit: int = 500) -> list[Memory]:
        cid = self._cid(character_id)
        limit = max(1, min(int(limit), 5000))
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT content, memory_type, importance, created_at, metadata
                FROM (
                    SELECT id, content, memory_type, importance, created_at, metadata
                    FROM memories WHERE character_id = ?
                    ORDER BY id DESC LIMIT ?
                ) ORDER BY id ASC""",
                (cid, limit),
            ).fetchall()
        return [self._row_to_memory(r) for r in rows]

    def search_memories(
        self, query: str, character_id: str | None = None, limit: int = 10
    ) -> list[Memory]:
        cid = self._cid(character_id)
        pattern = f"%{query.lower()}%"
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT content, memory_type, importance, created_at, metadata
                FROM memories
                WHERE character_id = ? AND LOWER(content) LIKE ?
                ORDER BY importance DESC, id DESC LIMIT ?""",
                (cid, pattern, limit),
            ).fetchall()
        return [self._row_to_memory(r) for r in rows]

    def promote_memories(self, threshold: float = 70.0) -> int:
        """Повышает короткие воспоминания до долгосрочных по важности."""
        with self._connect() as conn:
            cur = conn.execute(
                """UPDATE memories SET memory_type = 'long_term'
                WHERE memory_type = 'short_term' AND importance >= ?""",
                (threshold,),
            )
            return cur.rowcount

    def forget_memories(self, older_than_days: int = 30, importance_below: float = 30) -> int:
        cutoff = datetime.now().isoformat()
        with self._connect() as conn:
            cur = conn.execute(
                """DELETE FROM memories
                WHERE memory_type = 'short_term'
                  AND importance < ?
                  AND created_at < datetime('now', ?)""",
                (importance_below, f"-{older_than_days} days"),
            )
            _ = cutoff
            return cur.rowcount

    @staticmethod
    def _row_to_memory(row: sqlite3.Row) -> Memory:
        try:
            mt = MemoryType(row["memory_type"])
        except ValueError:
            mt = MemoryType.SHORT_TERM
        try:
            created = datetime.fromisoformat(row["created_at"])
        except (TypeError, ValueError):
            created = datetime.now()
        try:
            meta = json.loads(row["metadata"] or "{}")
        except (TypeError, ValueError):
            meta = {}
        return Memory(
            content=row["content"], memory_type=mt,
            importance=float(row["importance"]), created_at=created, metadata=meta,
        )

    # ---------- interactions ----------

    def save_interaction(self, user_message: str, assistant_message: str,
                         character_id: str | None = None) -> None:
        cid = self._cid(character_id)
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO interactions
                    (character_id, user_message, assistant_message, created_at)
                VALUES (?, ?, ?, ?)""",
                (cid, user_message, assistant_message, datetime.now().isoformat()),
            )

    def load_interactions(self, character_id: str | None = None,
                          limit: int = 50) -> list[dict[str, str]]:
        cid = self._cid(character_id)
        limit = max(1, min(int(limit), 500))
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT user_message, assistant_message FROM (
                    SELECT id, user_message, assistant_message FROM interactions
                    WHERE character_id = ? ORDER BY id DESC LIMIT ?
                ) ORDER BY id ASC""",
                (cid, limit),
            ).fetchall()
        history: list[dict[str, str]] = []
        for r in rows:
            history.append({"role": "user", "content": r["user_message"]})
            history.append({"role": "assistant", "content": r["assistant_message"]})
        return history

    # ---------- relationships ----------

    def save_relationship(self, other_name: str, rel: dict[str, float],
                          character_id: str | None = None) -> None:
        cid = self._cid(character_id)
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO relationships
                    (character_id, other_name, friendship, trust, respect, attachment, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(character_id, other_name) DO UPDATE SET
                    friendship=excluded.friendship, trust=excluded.trust,
                    respect=excluded.respect, attachment=excluded.attachment,
                    updated_at=excluded.updated_at""",
                (
                    cid, other_name,
                    float(rel.get("friendship", 0)), float(rel.get("trust", 0)),
                    float(rel.get("respect", 0)), float(rel.get("attachment", 0)),
                    datetime.now().isoformat(),
                ),
            )

    def load_relationships(self, character_id: str | None = None) -> list[dict[str, Any]]:
        cid = self._cid(character_id)
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT other_name, friendship, trust, respect, attachment "
                "FROM relationships WHERE character_id = ?", (cid,),
            ).fetchall()
        return [dict(r) for r in rows]

    # ---------- goals ----------

    def add_goal(self, goal_type: str, priority: float, description: str = "",
                 character_id: str | None = None) -> int:
        cid = self._cid(character_id)
        with self._connect() as conn:
            cur = conn.execute(
                """INSERT INTO goals (character_id, type, priority, description, created_at)
                VALUES (?, ?, ?, ?, ?)""",
                (cid, goal_type, float(priority), description, datetime.now().isoformat()),
            )
            return int(cur.lastrowid)

    def complete_goal(self, goal_id: int) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE goals SET status='completed', completed_at=? WHERE id=?",
                (datetime.now().isoformat(), goal_id),
            )

    def active_goals(self, character_id: str | None = None) -> list[dict[str, Any]]:
        cid = self._cid(character_id)
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, type, priority, description FROM goals "
                "WHERE character_id=? AND status='active' ORDER BY priority DESC",
                (cid,),
            ).fetchall()
        return [dict(r) for r in rows]

    # ---------- events ----------

    def log_event(self, event_type: str, payload: dict[str, Any] | None = None,
                  character_id: str | None = None) -> None:
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO events (character_id, event_type, payload, created_at)
                VALUES (?, ?, ?, ?)""",
                (
                    character_id, event_type,
                    json.dumps(payload or {}, ensure_ascii=False, default=str),
                    datetime.now().isoformat(),
                ),
            )

    def recent_events(self, limit: int = 50) -> list[dict[str, Any]]:
        limit = max(1, min(int(limit), 500))
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT event_type, payload, created_at FROM events "
                "ORDER BY id DESC LIMIT ?", (limit,),
            ).fetchall()
        return [dict(r) for r in rows]

    # ---------- settings ----------

    def set_setting(self, key: str, value: Any) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO settings (key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, json.dumps(value, ensure_ascii=False, default=str)),
            )

    def get_setting(self, key: str, default: Any = None) -> Any:
        with self._connect() as conn:
            row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        if not row:
            return default
        try:
            return json.loads(row["value"])
        except (TypeError, ValueError):
            return row["value"]

    # ---------- обслуживание ----------

    def backup(self, suffix: str | None = None) -> Path:
        stamp = suffix or datetime.now().strftime("%Y%m%d_%H%M%S")
        target = self.db_path.with_name(f"{self.db_path.stem}_backup_{stamp}.db")
        with self._connect() as src:
            dst = sqlite3.connect(target)
            with dst:
                src.backup(dst)
            dst.close()
        return target

    def vacuum(self) -> None:
        with self._connect() as conn:
            conn.execute("VACUUM")

    def stats(self) -> dict[str, int]:
        result = {}
        with self._connect() as conn:
            for table in ("characters", "memories", "interactions",
                          "relationships", "goals", "events"):
                row = conn.execute(f"SELECT COUNT(*) AS c FROM {table}").fetchone()
                result[table] = int(row["c"])
        return result