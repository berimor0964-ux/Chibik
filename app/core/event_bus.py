"""
Простая синхронная реализация EventBus.
Позже №1 или №2 заменит на настоящую.
"""
from typing import Callable, Type, Any


class EventBus:
    def __init__(self):
        self._subscribers: dict[Type, list[Callable]] = {}

    def subscribe(self, event_type: Type, handler: Callable[[Any], None]) -> None:
        self._subscribers.setdefault(event_type, []).append(handler)

    def unsubscribe(self, event_type: Type, handler: Callable) -> None:
        if event_type in self._subscribers:
            self._subscribers[event_type].remove(handler)

    def publish(self, event: Any) -> None:
        for handler in self._subscribers.get(type(event), []):
            try:
                handler(event)
            except Exception as e:
                print(f"[EventBus] handler error: {e}")