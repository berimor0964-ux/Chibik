"""Python/QML bridge: UI events, desktop world and character AI."""
from __future__ import annotations

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot

from app.core.event_bus import EventBus
from app.core.events import (
    CharacterMoved, CharacterChangedState, CharacterSpoke,
    ObjectCreated, ObjectRemoved, BuildingCreated,
    NeedChanged, NotificationCreated,
)
from app.ui.python import asset_manager
from app.ui.python.desktop_world import DesktopWorldController


class _WorkerSignals(QObject):
    finished = Signal(str)
    failed = Signal(str)


class _ChatWorker(QRunnable):
    def __init__(self, controller: DesktopWorldController, message: str):
        super().__init__()
        self.controller = controller
        self.message = message
        self.signals = _WorkerSignals()

    def run(self):
        try:
            response = self.controller.answer_chat(self.message)
        except Exception as error:
            response = f"Не удалось получить ответ AI: {error}"
            self.signals.failed.emit(response)
        else:
            self.signals.finished.emit(response)


class UiBridge(QObject):
    characterMoved = Signal(str, float, float)
    characterChangedState = Signal(str, str)
    characterSpoke = Signal(str, str)
    objectCreated = Signal(str, str, float, float)
    objectRemoved = Signal(str)
    buildingCreated = Signal(str, str, float, float)
    needChanged = Signal(str, str, float)
    notificationCreated = Signal(str, str)
    errorOccurred = Signal(str)

    # Сигналы экранного питомца.
    desktopPositionChanged = Signal(int, int)
    desktopStateChanged = Signal(str, str)
    speechRequested = Signal(str)
    needsUpdated = Signal(float, float, float)
    chatResponse = Signal(str)
    chatFailed = Signal(str)

    def __init__(self, event_bus: EventBus | None = None, parent=None):
        super().__init__(parent)
        self._event_bus = event_bus or EventBus()
        self._subscribe()
        self.controller = DesktopWorldController(self)
        self.controller.positionChanged.connect(self.desktopPositionChanged)
        self.controller.stateChanged.connect(self.desktopStateChanged)
        self.controller.speechRequested.connect(self.speechRequested)
        self.controller.needsChanged.connect(self.needsUpdated)
        self._thread_pool = QThreadPool.globalInstance()

    def _subscribe(self):
        self._event_bus.subscribe(CharacterMoved, self._on_char_moved)
        self._event_bus.subscribe(CharacterChangedState, self._on_char_state)
        self._event_bus.subscribe(CharacterSpoke, self._on_char_spoke)
        self._event_bus.subscribe(ObjectCreated, self._on_obj_created)
        self._event_bus.subscribe(ObjectRemoved, self._on_obj_removed)
        self._event_bus.subscribe(BuildingCreated, self._on_building_created)
        self._event_bus.subscribe(NeedChanged, self._on_need_changed)
        self._event_bus.subscribe(NotificationCreated, self._on_notification)

    def _on_char_moved(self, e: CharacterMoved):
        self.characterMoved.emit(str(e.character_id), float(e.x), float(e.y))

    def _on_char_state(self, e: CharacterChangedState):
        self.characterChangedState.emit(str(e.character_id), e.state)

    def _on_char_spoke(self, e: CharacterSpoke):
        self.characterSpoke.emit(str(e.character_id), e.text)

    def _on_obj_created(self, e: ObjectCreated):
        self.objectCreated.emit(str(e.object_id), e.type, float(e.x), float(e.y))

    def _on_obj_removed(self, e: ObjectRemoved):
        self.objectRemoved.emit(str(e.object_id))

    def _on_building_created(self, e: BuildingCreated):
        self.buildingCreated.emit(str(e.building_id), e.type, float(e.x), float(e.y))

    def _on_need_changed(self, e: NeedChanged):
        self.needChanged.emit(str(e.character_id), e.need, float(e.value))

    def _on_notification(self, e: NotificationCreated):
        self.notificationCreated.emit(e.title, e.text)

    @Slot(str, result="QVariantMap")
    def getCharacterMeta(self, character_id: str) -> dict:
        return asset_manager.load_character_meta(character_id)

    @Slot(str, str, result=str)
    def resolveCharacterSprite(self, character_id: str, state: str) -> str:
        return asset_manager.character_sprite_url(character_id, state)

    @Slot(str, result=str)
    def resolveObjectSprite(self, object_type: str) -> str:
        return asset_manager.object_sprite_url(object_type)

    @Slot(str)
    def sendChatMessage(self, text: str) -> None:
        text = (text or "").strip()
        if not text:
            return
        worker = _ChatWorker(self.controller, text)
        worker.signals.finished.connect(self.chatResponse)
        worker.signals.failed.connect(self.chatFailed)
        self._thread_pool.start(worker)

    @Slot(str, str)
    def characterAction(self, character_id: str, action: str) -> None:
        result = self.controller.perform_action(action)
        if result == "quit":
            self.notificationCreated.emit("Выход", "Закройте приложение через меню персонажа.")

    @Slot()
    def pauseMovement(self) -> None:
        self.controller.pause()

    @Slot()
    def resumeMovement(self) -> None:
        self.controller.resume()

    @Slot(int, int)
    def moveCharacterToWindowPosition(self, x: int, y: int) -> None:
        self.controller.set_window_position(x, y)

    @Slot()
    def requestWalk(self) -> None:
        self.controller.request_walk()

    @Slot(str)
    def requestRemoveObject(self, object_id: str) -> None:
        self._event_bus.publish(ObjectRemoved(object_id=object_id))

    def close(self) -> None:
        self.controller.close()
