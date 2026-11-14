import json
from pathlib import Path


# Корень проекта: .../desktop-pet/
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
ASSETS_ROOT = PROJECT_ROOT / "assets"


def _to_url(path: Path) -> str:
    """Превращает путь в file:// URL для QML."""
    return f"file:///{path.as_posix()}"


def character_sprite_url(character_id: str, state: str) -> str:
    """URL до спрайт-листа состояния."""
    path = ASSETS_ROOT / "characters" / character_id / f"{state}.png"
    if not path.exists():
        path = ASSETS_ROOT / "characters" / character_id / "idle.png"
    return _to_url(path)


def load_character_meta(character_id: str) -> dict:
    """Загружает meta.json персонажа."""
    path = ASSETS_ROOT / "characters" / character_id / "meta.json"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def object_sprite_url(object_type: str) -> str:
    """URL до спрайта объекта."""
    path = ASSETS_ROOT / "objects" / f"{object_type}.png"
    if not path.exists():
        path = ASSETS_ROOT / "objects" / "placeholder.png"
    return _to_url(path)