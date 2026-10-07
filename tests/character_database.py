import sqlite3

from pathlib import Path
from typing import Any

from app.character.character import Character
from app.character.memory import Memory, MemoryType


DATABASE_FILE = (
    Path(__file__).resolve().parent
    / "character_data.db"
)


class CharacterDatabase:
    """
    Временная SQLite-база для Character + AI.

    В будущем этот слой должен быть перенесён
    в app/database/ человеком №4.
    """

    def __init__(
        self,
        database_path: Path = DATABASE_FILE
    ):
        self.database_path = database_path
        self.initialize()

    def connect(self):
        return sqlite3.connect(
            self.database_path
        )

    # =========================================================
    # DATABASE INITIALIZATION
    # =========================================================

    def initialize(self):

        with self.connect() as connection:

            cursor = connection.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS character (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    age INTEGER NOT NULL
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS personality (
                    character_id INTEGER PRIMARY KEY,

                    friendliness REAL NOT NULL,
                    curiosity REAL NOT NULL,
                    laziness REAL NOT NULL,
                    humor REAL NOT NULL,
                    chaos REAL NOT NULL,
                    intelligence REAL NOT NULL,
                    bravery REAL NOT NULL,

                    traits TEXT NOT NULL,
                    backstory TEXT NOT NULL,
                    behavior_style TEXT NOT NULL,
                    likes TEXT NOT NULL,
                    dislikes TEXT NOT NULL,
                    rules TEXT NOT NULL,

                    FOREIGN KEY(character_id)
                        REFERENCES character(id)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    user_message TEXT NOT NULL,
                    assistant_message TEXT NOT NULL,

                    created_at
                    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    content TEXT NOT NULL,
                    memory_type TEXT NOT NULL,
                    importance REAL NOT NULL,

                    created_at
                    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            connection.commit()

    # =========================================================
    # HELPERS
    # =========================================================

    @staticmethod
    def list_to_text(
        values: list[str]
    ) -> str:

        return "\n".join(values)

    @staticmethod
    def text_to_list(
        value: str
    ) -> list[str]:

        return [
            item.strip()
            for item in value.splitlines()
            if item.strip()
        ]

    # =========================================================
    # CHARACTER
    # =========================================================

    def save_character(
        self,
        character: Character
    ):

        personality = character.personality

        with self.connect() as connection:

            cursor = connection.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO character (
                    id,
                    name,
                    age
                )
                VALUES (?, ?, ?)
            """, (
                1,
                character.name,
                character.age
            ))

            cursor.execute("""
                INSERT OR REPLACE INTO personality (
                    character_id,

                    friendliness,
                    curiosity,
                    laziness,
                    humor,
                    chaos,
                    intelligence,
                    bravery,

                    traits,
                    backstory,
                    behavior_style,
                    likes,
                    dislikes,
                    rules
                )
                VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?
                )
            """, (
                1,

                personality.friendliness,
                personality.curiosity,
                personality.laziness,
                personality.humor,
                personality.chaos,
                personality.intelligence,
                personality.bravery,

                self.list_to_text(
                    personality.traits
                ),

                personality.backstory,

                personality.behavior_style,

                self.list_to_text(
                    personality.likes
                ),

                self.list_to_text(
                    personality.dislikes
                ),

                self.list_to_text(
                    personality.rules
                )
            ))

            connection.commit()

    def load_character(self) -> Character | None:

        with self.connect() as connection:

            cursor = connection.cursor()

            cursor.execute("""
                SELECT
                    c.name,
                    c.age,

                    p.friendliness,
                    p.curiosity,
                    p.laziness,
                    p.humor,
                    p.chaos,
                    p.intelligence,
                    p.bravery,

                    p.traits,
                    p.backstory,
                    p.behavior_style,
                    p.likes,
                    p.dislikes,
                    p.rules

                FROM character c

                JOIN personality p
                    ON p.character_id = c.id

                WHERE c.id = 1
            """)

            row = cursor.fetchone()

        if row is None:
            return None

        (
            name,
            age,

            friendliness,
            curiosity,
            laziness,
            humor,
            chaos,
            intelligence,
            bravery,

            traits,
            backstory,
            behavior_style,
            likes,
            dislikes,
            rules
        ) = row

        character = Character(
            name=name,
            age=age
        )

        personality = character.personality

        personality.friendliness = friendliness
        personality.curiosity = curiosity
        personality.laziness = laziness
        personality.humor = humor
        personality.chaos = chaos
        personality.intelligence = intelligence
        personality.bravery = bravery

        personality.traits = self.text_to_list(
            traits
        )

        personality.backstory = backstory

        personality.behavior_style = (
            behavior_style
        )

        personality.likes = self.text_to_list(
            likes
        )

        personality.dislikes = self.text_to_list(
            dislikes
        )

        personality.rules = self.text_to_list(
            rules
        )

        return character

    # =========================================================
    # INTERACTIONS
    # =========================================================

    def save_interaction(
        self,
        user_message: str,
        assistant_message: str
    ):

        with self.connect() as connection:

            connection.execute("""
                INSERT INTO interactions (
                    user_message,
                    assistant_message
                )
                VALUES (?, ?)
            """, (
                user_message,
                assistant_message
            ))

            connection.commit()

    def get_recent_interactions(
        self,
        limit: int = 20
    ) -> list[tuple]:

        with self.connect() as connection:

            cursor = connection.cursor()

            cursor.execute("""
                SELECT
                    user_message,
                    assistant_message,
                    created_at
                FROM interactions
                ORDER BY id DESC
                LIMIT ?
            """, (
                limit,
            ))

            rows = cursor.fetchall()

        return list(
            reversed(rows)
        )

    # =========================================================
    # MEMORY
    # =========================================================

    def save_memory(
        self,
        memory: Memory
    ):

        with self.connect() as connection:

            connection.execute("""
                INSERT INTO memories (
                    content,
                    memory_type,
                    importance
                )
                VALUES (?, ?, ?)
            """, (
                memory.content,
                memory.memory_type.value,
                memory.importance
            ))

            connection.commit()

    def load_memories(
        self,
        limit: int = 100
    ) -> list[Memory]:

        with self.connect() as connection:

            cursor = connection.cursor()

            cursor.execute("""
                SELECT
                    content,
                    memory_type,
                    importance,
                    created_at
                FROM memories
                ORDER BY id DESC
                LIMIT ?
            """, (
                limit,
            ))

            rows = cursor.fetchall()

        result = []

        for (
            content,
            memory_type,
            importance,
            created_at
        ) in rows:

            try:
                memory_type_enum = MemoryType(
                    memory_type
                )
            except ValueError:
                memory_type_enum = (
                    MemoryType.LONG_TERM
                )

            memory = Memory(
                content=content,
                memory_type=memory_type_enum,
                importance=importance
            )

            result.append(memory)

        return result

    # =========================================================
    # DEVELOPMENT
    # =========================================================

    def clear_history(self):

        with self.connect() as connection:

            connection.execute(
                "DELETE FROM interactions"
            )

            connection.execute(
                "DELETE FROM memories"
            )

            connection.commit()

    def get_statistics(self) -> dict[str, Any]:

        with self.connect() as connection:

            cursor = connection.cursor()

            cursor.execute(
                "SELECT COUNT(*) FROM interactions"
            )

            interactions = cursor.fetchone()[0]

            cursor.execute(
                "SELECT COUNT(*) FROM memories"
            )

            memories = cursor.fetchone()[0]

        return {
            "interactions": interactions,
            "memories": memories
        }