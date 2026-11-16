import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from app.character.memory import Memory, MemoryType
from app.database.database import Database


@pytest.fixture
def db(tmp_path: Path) -> Database:
    database = Database(tmp_path / "test.db")
    database.create_character("mira", "Мира", 1)
    database.set_active_character("mira")
    return database


def test_create_and_list_characters(db: Database) -> None:
    db.create_character("tom", "Том", 2)
    ids = {c["id"] for c in db.list_characters()}
    assert {"mira", "tom"} <= ids


def test_save_and_load_state(db: Database) -> None:
    db.save_state({"energy": 42, "hunger": 70, "pos_x": 3.5, "scene_mode": "outside"})
    state = db.load_state()
    assert state["energy"] == 42
    assert state["scene_mode"] == "outside"


def test_personality_roundtrip(db: Database) -> None:
    db.save_personality({"friendliness": 0.8, "likes": ["чай", "музыка"]})
    p = db.load_personality()
    assert p["friendliness"] == 0.8
    assert "чай" in p["likes"]


def test_memories_and_search(db: Database) -> None:
    db.save_memory(Memory("Мира любит гулять", MemoryType.LONG_TERM, 90, datetime.now()))
    db.save_memory(Memory("Пользователь зовут Роман", MemoryType.EPISODIC, 80, datetime.now()))
    db.save_memory(Memory("Сегодня пасмурно", MemoryType.SHORT_TERM, 10, datetime.now()))
    found = db.search_memories("гулять")
    assert len(found) == 1
    assert found[0].importance == 90


def test_promote_memories(db: Database) -> None:
    db.save_memory(Memory("важное", MemoryType.SHORT_TERM, 80, datetime.now()))
    promoted = db.promote_memories(threshold=70)
    assert promoted == 1


def test_interactions_history(db: Database) -> None:
    db.save_interaction("привет", "Привет!")
    db.save_interaction("как дела", "Хорошо")
    history = db.load_interactions(limit=10)
    assert len(history) == 4
    assert history[0]["role"] == "user"
    assert history[-1]["content"] == "Хорошо"


def test_relationships_upsert(db: Database) -> None:
    db.save_relationship("Роман", {"friendship": 50, "trust": 40})
    db.save_relationship("Роман", {"friendship": 70, "trust": 60})
    rels = db.load_relationships()
    assert len(rels) == 1
    assert rels[0]["friendship"] == 70


def test_goals_lifecycle(db: Database) -> None:
    gid = db.add_goal("SLEEP", 100, "Отдохнуть")
    assert len(db.active_goals()) == 1
    db.complete_goal(gid)
    assert len(db.active_goals()) == 0


def test_events_log(db: Database) -> None:
    db.log_event("CharacterMoved", {"x": 1, "y": 2})
    db.log_event("CharacterSpoke", {"text": "мяу"})
    assert len(db.recent_events()) == 2


def test_settings_kv(db: Database) -> None:
    db.set_setting("volume", 0.7)
    assert db.get_setting("volume") == 0.7
    db.set_setting("volume", 0.9)
    assert db.get_setting("volume") == 0.9
    assert db.get_setting("missing", "default") == "default"


def test_backup_creates_file(db: Database, tmp_path: Path) -> None:
    db.save_interaction("a", "b")
    backup = db.backup()
    assert backup.exists()
    assert backup.stat().st_size > 0


def test_cascade_delete(tmp_path: Path) -> None:
    db = Database(tmp_path / "cascade.db")
    db.create_character("temp", "Temp")
    db.set_active_character("temp")
    db.save_memory(Memory("x", MemoryType.SHORT_TERM, 50, datetime.now()))
    db.save_interaction("a", "b")
    with db._connect() as conn:
        conn.execute("DELETE FROM characters WHERE id = 'temp'")
    assert db.load_memories("temp") == []
    assert db.load_interactions("temp") == []