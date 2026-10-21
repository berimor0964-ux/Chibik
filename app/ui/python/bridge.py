from PySide6.QtCore import QObject, Signal, Slot

from app.core.event_bus import EventBus
from app.core.events import (
    CharacterMoved, CharacterChangedState, CharacterSpoke,
    ObjectCreated, ObjectRemoved, BuildingCreated,
    NeedChanged, NotificationCreated,
)
from app.ui.python import asset_manager


class UiBridge(QObject):
    # ---- Сигналы для QML ----
    characterMoved = Signal(str, float, float)
    characterChangedState = Signal(str, str)
    characterSpoke = Signal(str, str)

    objectCreated = Signal(str, str, float, float)
    objectRemoved = Signal(str)
    buildingCreated = Signal(str, str, float, float)

    needChanged = Signal(str, str, float)
    notificationCreated = Signal(str, str)

    # ---- Служебные ----
    errorOccurred = Signal(str)

    def __init__(self, event_bus: EventBus, parent=None):
        super().__init__(parent)
        self._event_bus = event_bus
        self._subscribe()

    def _subscribe(self):
        self._event_bus.subscribe(CharacterMoved, self._on_char_moved)
        self._event_bus.subscribe(CharacterChangedState, self._on_char_state)
        self._event_bus.subscribe(CharacterSpoke, self._on_char_spoke)
        self._event_bus.subscribe(ObjectCreated, self._on_obj_created)
        self._event_bus.subscribe(ObjectRemoved, self._on_obj_removed)
        self._event_bus.subscribe(BuildingCreated, self._on_building_created)
        self._event_bus.subscribe(NeedChanged, self._on_need_changed)
        self._event_bus.subscribe(NotificationCreated, self._on_notification)

    # ---- Обработчики ----
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

    # ---- Слоты, вызываемые из QML ----

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
        """
        Отправка сообщения в AI.
        Пока заглушка — эхом отдаём в CharacterSpoke через event_bus.
        Когда №2 будет готов — раскомментируй вызов.
        """
        print(f"[UI] User said: {text}")

        # Демо-эхо:
        from app.core.events import CharacterSpoke
        self._event_bus.publish(CharacterSpoke(
            character_id="lyra",
            text=f"Ты сказал: {text}. (Заглушка AI)",
        ))

        # Когда №2 будет готов:
        # from app.character.character import character_api
        # character_api.chat(text)

    @Slot(str, str)
    def characterAction(self, character_id: str, action: str) -> None:
        """Клик по пункту контекстного меню персонажа."""
        print(f"[UI] Action '{action}' for character {character_id}")
        # Когда №2 будет готов:
        # character_api.perform_action(character_id, action)

    @Slot(str, float, float)
    def requestSpawnObject(self, object_type: str, x: float, y: float) -> None:
        """Запрос создания объекта через редактор мира."""
        print(f"[UI] Spawn request: {object_type} at ({x}, {y})")
        # Когда №1 будет готов:
        # world_api.spawn_object(object_type, (x, y))
        # А пока — эмулируем через EventBus, чтобы посмотреть в UI:
        from app.core.events import ObjectCreated
        import uuid
        self._event_bus.publish(ObjectCreated(
            object_id=str(uuid.uuid4())[:8],
            type=object_type,
            x=x, y=y,
        ))

    @Slot(str)
    def requestRemoveObject(self, object_id: str) -> None:
        print(f"[UI] Remove request: {object_id}")
        from app.core.events import ObjectRemoved
        self._event_bus.publish(ObjectRemoved(object_id=object_id))