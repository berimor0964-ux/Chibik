"""Поиск пути в двумерной зоне с помощью алгоритма A*."""

from heapq import heappop, heappush
from itertools import count

from .objects import WorldObject
from .zone import Zone

Position = tuple[float, float]


class Pathfinding:
    """Поиск маршрута по сетке с обходом твёрдых препятствий."""

    @staticmethod
    def find_path(
        zone: Zone,
        start: Position,
        goal: Position,
        width: float = 1.0,
        height: float = 1.0,
        solid: bool = True,
        ignore_object_id: str | None = None,
        step: float = 1.0,
    ) -> list[Position] | None:
        """Возвращает путь от start до goal, включая обе точки.

        Возвращает None, если маршрут недоступен.
        Движение разрешено только по четырём направлениям.
        Координаты соседних узлов отличаются на step.
        """
        if step <= 0 or width <= 0 or height <= 0:
            raise ValueError("Размеры и шаг должны быть положительными.")

        start = (float(start[0]), float(start[1]))
        goal = (float(goal[0]), float(goal[1]))

        def make_object(position: Position) -> WorldObject:
            return WorldObject(
                x=position[0],
                y=position[1],
                width=width,
                height=height,
                solid=solid,
            )

        def is_walkable(position: Position) -> bool:
            candidate = make_object(position)

            if not zone.contains(candidate):
                return False

            if solid:
                for other in zone.objects.values():
                    if other.id == ignore_object_id:
                        continue
                    if not other.solid:
                        continue
                    if candidate.intersects(other):
                        return False

            return True

        if not is_walkable(start) or not is_walkable(goal):
            return None

        if start == goal:
            return [start]

        def heuristic(position: Position) -> float:
            return (
                abs(position[0] - goal[0])
                + abs(position[1] - goal[1])
            ) / step

        def normalize(position: Position) -> Position:
            return (round(position[0], 8), round(position[1], 8))

        open_heap: list[tuple[float, int, Position]] = []
        sequence = count()
        heappush(open_heap, (heuristic(start), next(sequence), start))

        came_from: dict[Position, Position] = {}
        g_score: dict[Position, float] = {start: 0.0}
        closed: set[Position] = set()

        directions = (
            (step, 0.0),
            (-step, 0.0),
            (0.0, step),
            (0.0, -step),
        )

        while open_heap:
            _, _, current = heappop(open_heap)

            if current in closed:
                continue

            if current == goal:
                path = [current]
                while current in came_from:
                    current = came_from[current]
                    path.append(current)
                path.reverse()
                return path

            closed.add(current)

            for dx, dy in directions:
                neighbor = normalize((current[0] + dx, current[1] + dy))

                if neighbor in closed or not is_walkable(neighbor):
                    continue

                tentative_g = g_score[current] + 1.0

                if tentative_g >= g_score.get(neighbor, float("inf")):
                    continue

                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                priority = tentative_g + heuristic(neighbor)
                heappush(
                    open_heap,
                    (priority, next(sequence), neighbor),
                )

        return None