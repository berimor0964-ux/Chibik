"""Базовые объекты игрового мира."""

from dataclasses import dataclass, field
from uuid import uuid4


@dataclass
class WorldObject:
    """Объект с прямоугольными границами в двумерном мире."""

    x: float = 0.0
    y: float = 0.0
    width: float = 1.0
    height: float = 1.0
    solid: bool = True
    name: str = "Объект"
    id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError(
                "Размеры объекта должны быть положительными."
            )

    @property
    def right(self) -> float:
        return self.x + self.width

    @property
    def bottom(self) -> float:
        return self.y + self.height

    def intersects(self, other: "WorldObject") -> bool:
        """Проверяет пересечение двух прямоугольников."""
        return (
            self.x < other.right
            and self.right > other.x
            and self.y < other.bottom
            and self.bottom > other.y
        )