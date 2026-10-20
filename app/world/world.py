
"""Управление игровым миром."""

from dataclasses import dataclass, field

from .objects import WorldObject
from .zone import Zone


@dataclass
class World:
    name: str = "Мир"
    zones: dict[str, Zone] = field(default_factory=dict)

    def add_zone(self, zone: Zone) -> None:
        """Добавляет зону в мир."""
        if zone.name in self.zones:
            raise ValueError(
                f"Зона '{zone.name}' уже существует."
            )

        self.zones[zone.name] = zone

    def get_zone(self, name: str) -> Zone:
        """Возвращает зону по имени."""
        try:
            return self.zones[name]
        except KeyError:
            raise KeyError(
                f"Зона '{name}' не найдена."
            ) from None

    def add_object(
        self,
        zone_name: str,
        obj: WorldObject,
    ) -> None:
        """Добавляет объект в указанную зону."""
        self.get_zone(zone_name).add_object(obj)

    def find_object(self, object_id: str) -> WorldObject | None:
        """Ищет объект во всех зонах мира."""
        for zone in self.zones.values():
            if object_id in zone.objects:
                return zone.objects[object_id]

        return None
