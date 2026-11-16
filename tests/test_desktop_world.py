"""Smoke tests for the world rules used by the desktop pet."""
import unittest

from app.character.behavior import Behavior
from app.character.character import Character
from app.character.actions import ActionType
from app.world.navigation import Navigation
from app.world.objects import WorldObject
from app.world.physics import Physics
from app.world.world import World
from app.world.zone import Zone


class DesktopWorldTests(unittest.TestCase):
    def setUp(self):
        self.world = World("Рабочий стол")
        self.zone = Zone("Экран", width=40, height=24)
        self.world.add_zone(self.zone)
        self.pet = WorldObject(x=36, y=20, width=4, height=4, name="Мира")
        self.world.add_object(self.zone.name, self.pet)

    def test_pathfinder_returns_route_across_screen(self):
        path = Navigation.find_path(self.pet, self.zone, 2, 2)
        self.assertIsNotNone(path)
        self.assertEqual(path[0], (36.0, 20.0))
        self.assertEqual(path[-1], (2.0, 2.0))

    def test_physics_prevents_leaving_screen(self):
        self.assertFalse(Physics.can_move(self.pet, self.zone, 37, 20))
        self.assertTrue(Physics.can_move(self.pet, self.zone, 35.5, 20))

    def test_behavior_selects_sleep_when_energy_is_low(self):
        character = Character(name="Мира", age=1)
        character.needs.energy = 10
        action = Behavior(character).update()
        self.assertIsNotNone(action)
        self.assertEqual(action.type, ActionType.SLEEP)

    def test_behavior_selects_food_when_hungry_and_not_exhausted(self):
        character = Character(name="Мира", age=1)
        character.needs.energy = 70
        character.needs.hunger = 10
        action = Behavior(character).update()
        self.assertIsNotNone(action)
        self.assertEqual(action.type, ActionType.EAT)


if __name__ == "__main__":
    unittest.main()
