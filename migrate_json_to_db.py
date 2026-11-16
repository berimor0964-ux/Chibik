"""
Миграция данных из data/mira_state.json в SQLite базу desktop_pet.db.
Запускается один раз при первом переходе на новую систему хранения.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

# Добавляем корень проекта в путь
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.database.database import Database
from app.character.memory import Memory, MemoryType


def migrate() -> None:
    """Переносит данные из JSON в SQLite."""
    json_path = PROJECT_ROOT / "data" / "mira_state.json"

    print("=" * 60)
    print("МИГРАЦИЯ ДАННЫХ: JSON → SQLite")
    print("=" * 60)

    # Проверяем существование JSON
    if not json_path.exists():
        print(f"❌ Файл не найден: {json_path}")
        print("Миграция не требуется или файл был удалён.")
        return

    # Загружаем JSON
    print(f"📂 Читаем: {json_path}")
    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"❌ Ошибка чтения JSON: {e}")
        return

    # Создаём/открываем базу
    db = Database()
    character_id = "mira"

    print(f"🗄️  База данных: {db.db_path}")

    # Создаём персонажа (если ещё не создан)
    db.create_character(character_id, "Мира", age=1)
    db.set_active_character(character_id)

    # 1. Миграция состояния (needs + position + mood)
    print("\n📊 Миграция состояния...")
    position = data.get("position", {})
    needs = data.get("needs", {})

    state = {
        "energy": needs.get("energy", 100),
        "hunger": needs.get("hunger", 100),
        "fun": needs.get("fun", 100),
        "social": needs.get("social", 100),
        "hygiene": needs.get("hygiene", 100),
        "comfort": needs.get("comfort", 100),
        "pos_x": position.get("x", 0),
        "pos_y": position.get("y", 0),
        "scene_mode": "room",
        "mood": data.get("mood", "neutral"),
    }

    db.save_state(state, character_id)
    print(f"   ✅ Энергия: {state['energy']:.1f}")
    print(f"   ✅ Голод: {state['hunger']:.1f}")
    print(f"   ✅ Позиция: ({state['pos_x']}, {state['pos_y']})")

    # 2. Миграция личности
    print("\n🎭 Миграция личности...")
    personality = data.get("personality", {})

    pers = {
        "friendliness": personality.get("friendliness", 50),
        "curiosity": personality.get("curiosity", 50),
        "laziness": personality.get("laziness", 50),
        "humor": personality.get("humor", 50),
        "chaos": personality.get("chaos", 50),
        "intelligence": personality.get("intelligence", 50),
        "courage": personality.get("bravery", 50),  # bravery → courage
        "backstory": personality.get("backstory", ""),
        "style": personality.get("behavior_style", ""),
        "likes": personality.get("likes", []),
        "dislikes": personality.get("dislikes", []),
        "rules": personality.get("rules", []),
    }

    db.save_personality(pers, character_id)
    print(f"   ✅ Дружелюбие: {pers['friendliness']}")
    print(f"   ✅ Любопытство: {pers['curiosity']}")
    print(f"   ✅ Предыстория: {pers['backstory'][:50]}...")

    # 3. Миграция воспоминаний
    print("\n💭 Миграция воспоминаний...")
    memories = data.get("memories", [])
    migrated_count = 0

    for mem_data in memories:
        content = mem_data.get("content", "")
        if not content:
            continue

        # Определяем тип памяти
        mem_type_str = mem_data.get("type", "short_term")
        try:
            mem_type = MemoryType(mem_type_str)
        except ValueError:
            mem_type = MemoryType.SHORT_TERM

        # Создаём объект Memory
        memory = Memory(
            content=content,
            memory_type=mem_type,
            importance=float(mem_data.get("importance", 50)),
            created_at=datetime.now(),  # JSON не хранит дату
            metadata=mem_data.get("metadata", {}),
        )

        db.save_memory(memory, character_id)
        migrated_count += 1

    print(f"   ✅ Перенесено воспоминаний: {migrated_count}")

    # 4. Обновляем last_seen
    db.touch_character(character_id)

    # 5. Показываем статистику
    print("\n📈 Статистика базы данных:")
    stats = db.stats()
    for table, count in stats.items():
        print(f"   • {table}: {count}")

    # 6. Создаём резервную копию JSON
    backup_path = json_path.with_suffix(".json.backup")
    json_path.rename(backup_path)
    print(f"\n💾 Резервная копия JSON: {backup_path}")

    print("\n" + "=" * 60)
    print("✅ МИГРАЦИЯ ЗАВЕРШЕНА УСПЕШНО!")
    print("=" * 60)
    print("\nТеперь можно удалить файл migrate_json_to_db.py")
    print("и запустить приложение: python main.py")


if __name__ == "__main__":
    try:
        migrate()
    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)