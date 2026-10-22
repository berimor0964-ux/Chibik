"""Навигация объектов по зонам игрового мира."""

from .objects import WorldObject
from .pathfinding import Pathfinding
from .zone import Zone


class Navigation:
    """Предоставляет объектам мира поиск доступных маршрутов."""

    @staticmethod
    def find_path(
        obj: WorldObject,
        zone: Zone,
        target_x: float,
        target_y: float,
        step: float = 1.0,
    ) -> list[tuple[float, float]] | None:
        """Находит маршрут объекта до заданных координат."""
        if zone.objects.get(obj.id) is not obj:
            raise ValueError("Объект не принадлежит указанной зоне.")

        return Pathfinding.find_path(
            zone=zone,
            start=(obj.x, obj.y),
            goal=(target_x, target_y),
            width=obj.width,
            height=obj.height,
            solid=obj.solid,
            ignore_object_id=obj.id,
            step=step,
        )