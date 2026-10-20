
import unittest

from app.world.navigation import Navigation
from app.world.objects import WorldObject
from app.world.pathfinding import Pathfinding
from app.world.zone import Zone


class PathfindingTests(unittest.TestCase):
    def setUp(self):
        self.zone = Zone("Комната", width=8, height=8)

    def test_finds_straight_path(self):
        path = Pathfinding.find_path(
            self.zone, (0, 0), (3, 0)
        )

        self.assertEqual(path, [(0, 0), (1, 0), (2, 0), (3, 0)])

    def test_routes_around_wall(self):
        wall = WorldObject(x=2, y=0, width=1, height=3, name="Стена")
        self.zone.add_object(wall)

        path = Pathfinding.find_path(
            self.zone, (1, 1), (4, 1)
        )

        self.assertIsNotNone(path)
        self.assertEqual(path[0], (1, 1))
        self.assertEqual(path[-1], (4, 1))

        for x, y in path:
            candidate = WorldObject(x=x, y=y)
            self.assertFalse(candidate.intersects(wall))

    def test_returns_none_for_blocked_goal(self):
        wall = WorldObject(x=3, y=0, width=1, height=8)
        self.zone.add_object(wall)

        path = Pathfinding.find_path(
            self.zone, (1, 1), (4, 1)
        )

        self.assertIsNone(path)

    def test_rejects_goal_outside_zone(self):
        path = Pathfinding.find_path(
            self.zone, (1, 1), (8, 1)
        )

        self.assertIsNone(path)

    def test_navigation_uses_object_position(self):
        obj = WorldObject(x=0, y=0, name="Игрок")
        self.zone.add_object(obj)

        path = Navigation.find_path(obj, self.zone, 3, 0)

        self.assertEqual(path, [(0, 0), (1, 0), (2, 0), (3, 0)])

    def test_rejects_object_from_another_zone(self):
        obj = WorldObject(x=0, y=0)

        with self.assertRaises(ValueError):
            Navigation.find_path(obj, self.zone, 3, 0)


if __name__ == "__main__":
    unittest.main()
