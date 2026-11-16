from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_all_character_animation_frames_exist():
    frames = ROOT / "assets" / "characters" / "chibik"
    for state in ("idle", "stand", "sleep", "walk_left", "walk_right"):
        for frame in (1, 2):
            assert (frames / f"{state}_{frame:02d}.png").is_file()


def test_qml_context_properties_are_provided_by_entry_point():
    entry = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
    qml = (ROOT / "app" / "ui" / "qml" / "Main.qml").read_text(encoding="utf-8")
    character = (ROOT / "app" / "ui" / "qml" / "components" / "Character.qml").read_text(encoding="utf-8")
    for name in ("assetsUrl", "houseX", "houseY", "houseWidth", "houseHeight"):
        assert name in entry
    for name in ("houseX", "houseY", "houseWidth", "houseHeight"):
        assert name in qml
    assert "assetsUrl" in character


def test_file_drop_uses_recoverable_system_recycle_bin():
    bridge = (ROOT / "app" / "ui" / "python" / "bridge.py").read_text(encoding="utf-8")
    handler = (ROOT / "app" / "ui" / "python" / "file_drop.py").read_text(encoding="utf-8")
    character = (ROOT / "app" / "ui" / "qml" / "components" / "Character.qml").read_text(encoding="utf-8")
    assert "move_file_to_recycle_bin" in bridge
    assert "send2trash" in handler
    assert "path.unlink" not in handler
    assert "path.rename" not in handler
    assert "bridge.eatFile" in character


def test_speech_bubble_tracks_character_position():
    main_qml = (ROOT / "app" / "ui" / "qml" / "Main.qml").read_text(encoding="utf-8")
    bubble = (ROOT / "app" / "ui" / "qml" / "components" / "SpeechBubble.qml").read_text(encoding="utf-8")
    assert "bubble.updateAnchor" in main_qml
    assert "function updateAnchor" in bubble


def test_walk_changes_between_room_and_outdoor_scene():
    controller = (ROOT / "app" / "ui" / "python" / "desktop_world.py").read_text(encoding="utf-8")
    main_qml = (ROOT / "app" / "ui" / "qml" / "Main.qml").read_text(encoding="utf-8")
    assert 'self._transition_after_path = "outside"' in controller
    assert 'self._transition_after_path = "room"' in controller
    assert 'rootWindow.sceneMode === "outside"' in main_qml
    assert 'action: "home"' in (ROOT / "app" / "ui" / "qml" / "components" / "ContextMenu.qml").read_text(encoding="utf-8")
