
import unittest

from app.world.objects import WorldObject
from app.world.physics import Physics
from app.world.world import World
from app.world.zone import Zone


class WorldEngineTests(unittest.TestCase):
    def setUp(self):
        self.world = World("Тестовый мир")
        self.zone = Zone("Комната", width=10, height=10)
        self.world.add_zone(self.zone)

    def test_add_zone_and_find_it(self):
        self.assertIs(
            self.world.get_zone("Комната"),
            self.zone,
        )

    def test_add_object_inside_zone(self):
        obj = WorldObject(x=2, y=3, name="Стол")
        self.world.add_object("Комната", obj)

        self.assertIs(self.world.find_object(obj.id), obj)

    def test_reject_object_outside_zone(self):
        obj = WorldObject(x=9.5, y=0, width=1, height=1)

        with self.assertRaises(ValueError):
            self.world.add_object("Комната", obj)

    def test_move_without_collision(self):
        obj = WorldObject(x=1, y=1)
        self.zone.add_object(obj)

        result = Physics.move(obj, self.zone, 2, 0)

        self.assertTrue(result)
        self.assertEqual(obj.x, 3)

    def test_blocked_by_solid_object(self):
        player = WorldObject(x=0, y=0)
        wall = WorldObject(x=2, y=0, name="Стена")

        self.zone.add_object(player)
        self.zone.add_object(wall)

        result = Physics.move(player, self.zone, 1.5, 0)

        self.assertFalse(result)
        self.assertEqual(player.x, 0)

    def test_cannot_leave_zone(self):
        obj = WorldObject(x=8, y=8)
        self.zone.add_object(obj)

        result = Physics.move(obj, self.zone, 2, 0)

        self.assertFalse(result)
        self.assertEqual(obj.x, 8)


if __name__ == "__main__":
    unittest.main()
