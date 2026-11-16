"""Python/QML bridge: desktop pet, AI chat, voice input and file drop."""
from __future__ import annotations

import threading
import uuid
from pathlib import Path
from urllib.parse import urlparse

from PySide6.QtCore import QObject, QRunnable, QThread, QThreadPool, QUrl, Signal, Slot

from app.core.event_bus import EventBus
from app.core.events import (
    CharacterMoved, CharacterChangedState, CharacterSpoke,
    ObjectCreated, ObjectRemoved, BuildingCreated,
    NeedChanged, NotificationCreated,
)
from app.ui.python import asset_manager
from app.ui.python.desktop_world import DesktopWorldController
from app.ui.python.file_drop import move_file_to_recycle_bin


class _WorkerSignals(QObject):
    finished = Signal(str)
    failed = Signal(str)


class _ChatWorker(QRunnable):
    """Runs AI chat outside the Qt UI thread."""
    def __init__(self, controller: DesktopWorldController, message: str):
        super().__init__()
        self.controller = controller
        self.message = message
        self.signals = _WorkerSignals()

    def run(self):
        try:
            self.signals.finished.emit(self.controller.answer_chat(self.message))
        except Exception as error:
            self.signals.failed.emit(f"Не удалось получить ответ AI: {error}")


class _VoiceWorker(QThread):
    transcript = Signal(str)
    status = Signal(str)
    failed = Signal(str)

    def __init__(self):
        super().__init__()
        self._stop_event = threading.Event()
        self._stt = None

    def run(self):
        try:
            from app.voice.stt import SpeechToText
            self.status.emit("Загружаю распознавание речи…")
            # CPU/int8 работает и на компьютерах без CUDA.
            self._stt = SpeechToText(
                model_size="base", device="cpu", compute_type="int8"
            )
            self._stt.start(self.transcript.emit)
            self.status.emit("Слушаю… говори с Мирой")
            while not self._stop_event.wait(0.2):
                if not self._stt.running:
                    break
            self._stt.stop()
            self.status.emit("Микрофон выключен")
        except Exception as error:
            self.failed.emit(f"Микрофон недоступен: {error}")
            self.status.emit("Микрофон выключен")

    def stop(self):
        self._stop_event.set()
        if self._stt is not None:
            self._stt.stop()


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

    desktopPositionChanged = Signal(int, int)
    desktopStateChanged = Signal(str, str)
    speechRequested = Signal(str)
    needsUpdated = Signal(float, float, float)
    chatResponse = Signal(str)
    chatFailed = Signal(str)
    voiceTranscript = Signal(str)
    voiceStatus = Signal(str)
    fileConsumed = Signal(str, bool, str)
    desktopSceneChanged = Signal(str)

    def __init__(self, event_bus: EventBus | None = None, parent=None):
        super().__init__(parent)
        self._event_bus = event_bus or EventBus()
        self._subscribe()
        self.controller = DesktopWorldController(self)
        self.controller.positionChanged.connect(self.desktopPositionChanged)
        self.controller.stateChanged.connect(self.desktopStateChanged)
        self.controller.speechRequested.connect(self.speechRequested)
        self.controller.needsChanged.connect(self.needsUpdated)
        self.controller.sceneChanged.connect(self.desktopSceneChanged)
        self._thread_pool = QThreadPool.globalInstance()
        self._voice_worker: _VoiceWorker | None = None

    def _subscribe(self):
        subscriptions = (
            (CharacterMoved, self._on_char_moved),
            (CharacterChangedState, self._on_char_state),
            (CharacterSpoke, self._on_char_spoke),
            (ObjectCreated, self._on_obj_created),
            (ObjectRemoved, self._on_obj_removed),
            (BuildingCreated, self._on_building_created),
            (NeedChanged, self._on_need_changed),
            (NotificationCreated, self._on_notification),
        )
        for event_type, callback in subscriptions:
            self._event_bus.subscribe(event_type, callback)

    def _on_char_moved(self, e): self.characterMoved.emit(str(e.character_id), float(e.x), float(e.y))
    def _on_char_state(self, e): self.characterChangedState.emit(str(e.character_id), e.state)
    def _on_char_spoke(self, e): self.characterSpoke.emit(str(e.character_id), e.text)
    def _on_obj_created(self, e): self.objectCreated.emit(str(e.object_id), e.type, float(e.x), float(e.y))
    def _on_obj_removed(self, e): self.objectRemoved.emit(str(e.object_id))
    def _on_building_created(self, e): self.buildingCreated.emit(str(e.building_id), e.type, float(e.x), float(e.y))
    def _on_need_changed(self, e): self.needChanged.emit(str(e.character_id), e.need, float(e.value))
    def _on_notification(self, e): self.notificationCreated.emit(e.title, e.text)

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
        if text:
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
    def pauseMovement(self): self.controller.pause()
    @Slot()
    def resumeMovement(self): self.controller.resume()
    @Slot(int, int)
    def moveCharacterToWindowPosition(self, x: int, y: int): self.controller.set_window_position(x, y)
    @Slot()
    def requestWalk(self): self.controller.request_walk()

    @Slot(bool)
    def setAutoRotate(self, enabled: bool):
        self.controller.set_auto_rotate(enabled)

    @Slot(bool)
    def setVoiceEnabled(self, enabled: bool):
        if enabled:
            if self._voice_worker and self._voice_worker.isRunning():
                return
            self._voice_worker = _VoiceWorker()
            self._voice_worker.transcript.connect(self._on_voice_transcript)
            self._voice_worker.status.connect(self.voiceStatus)
            self._voice_worker.failed.connect(self._on_voice_error)
            self._voice_worker.start()
        elif self._voice_worker:
            self._voice_worker.stop()
            self._voice_worker.wait(4000)
            self._voice_worker = None

    @Slot(str)
    def _on_voice_transcript(self, text: str):
        text = (text or "").strip()
        if text:
            self.voiceTranscript.emit(text)
            self.sendChatMessage(text)

    def _on_voice_error(self, message: str):
        self.voiceStatus.emit(message)
        self.chatFailed.emit(message)

    @Slot(str)
    def eatFile(self, url: str):
        """Перемещает сброшенный на Миру файл в системную Корзину."""
        display_name = "Файл"
        try:
            parsed = urlparse(url)
            if parsed.scheme.lower() != "file":
                raise ValueError("Можно отправлять в Корзину только локальные файлы.")
            local_path = QUrl(url).toLocalFile()
            if not local_path:
                raise ValueError("Не удалось прочитать путь к файлу.")
            path = Path(local_path)
            display_name = path.name or display_name
            move_file_to_recycle_bin(path)
            message = f"Ням! «{display_name}» отправлен в Корзину. Его можно восстановить."
            self.fileConsumed.emit(display_name, True, message)
            self.speechRequested.emit(f"Ням-ням! Я отправила «{display_name}» в Корзину. ♥")
        except Exception as error:
            self.fileConsumed.emit(display_name, False, str(error))
            self.speechRequested.emit(f"Не получилось съесть файл: {error}")

    @Slot(str, float, float)
    def requestSpawnObject(self, object_type: str, x: float, y: float):
        self._event_bus.publish(ObjectCreated(object_id=str(uuid.uuid4())[:8], type=object_type, x=x, y=y))

    @Slot(str)
    def requestRemoveObject(self, object_id: str):
        self._event_bus.publish(ObjectRemoved(object_id=object_id))

    def close(self):
        if self._voice_worker:
            self._voice_worker.stop()
            self._voice_worker.wait(4000)
            self._voice_worker = None
        self.controller.close()
