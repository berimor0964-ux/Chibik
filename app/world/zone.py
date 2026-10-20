
"""Зона игрового мира."""

from dataclasses import dataclass, field

from .objects import WorldObject


@dataclass
class Zone:
    name: str
    x: float = 0.0
    y: float = 0.0
    width: float = 100.0
    height: float = 100.0
    objects: dict[str, WorldObject] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError(
                "Размеры зоны должны быть положительными."
            )

    def contains(self, obj: WorldObject) -> bool:
        """Проверяет, полностью ли объект находится внутри зоны."""
        return (
            obj.x >= self.x
            and obj.y >= self.y
            and obj.right <= self.x + self.width
            and obj.bottom <= self.y + self.height
        )

    def add_object(self, obj: WorldObject) -> None:
        """Добавляет объект в зону."""
        if obj.id in self.objects:
            raise ValueError(
                f"Объект с ID {obj.id} уже находится в зоне."
            )

        if not self.contains(obj):
            raise ValueError("Объект находится за границами зоны.")

        self.objects[obj.id] = obj

    def remove_object(self, object_id: str) -> WorldObject:
        """Удаляет объект из зоны и возвращает его."""
        try:
            return self.objects.pop(object_id)
        except KeyError:
            raise KeyError(
                f"Объект {object_id} не найден в зоне."
            ) from None
