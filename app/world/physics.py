"""Простая двумерная физика игрового мира."""

from .objects import WorldObject
from .zone import Zone


class Physics:
    @staticmethod
    def can_move(
        obj: WorldObject,
        zone: Zone,
        new_x: float,
        new_y: float,
    ) -> bool:
        """Проверяет допустимость перемещения объекта."""
        candidate = WorldObject(
            x=new_x,
            y=new_y,
            width=obj.width,
            height=obj.height,
            solid=obj.solid,
            name=obj.name,
            id=obj.id,
        )

        if not zone.contains(candidate):
            return False

        if obj.solid:
            for other in zone.objects.values():
                if other.id == obj.id or not other.solid:
                    continue

                if candidate.intersects(other):
                    return False

        return True

    @classmethod
    def move(
        cls,
        obj: WorldObject,
        zone: Zone,
        dx: float,
        dy: float,
    ) -> bool:
        """Перемещает объект; возвращает True при успехе."""
        if zone.objects.get(obj.id) is not obj:
            raise ValueError(
                "Объект не принадлежит указанной зоне."
            )

        new_x = obj.x + dx
        new_y = obj.y + dy

        if not cls.can_move(obj, zone, new_x, new_y):
            return False

        obj.x = new_x
        obj.y = new_y
        return True