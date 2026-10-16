from dataclasses import dataclass

from app.character.actions import Action
from app.character.behavior import Behavior
from app.character.character import Character
from app.character.goals import Goal

from .context import AIContext


@dataclass
class Plan:

    goal: Goal

    actions: list[Action]


class Planner:

    def plan(
        self,
        character: Character,
        context: AIContext
    ) -> Plan | None:

        behavior = Behavior(
            character
        )

        goal = behavior.evaluate()

        if goal is None:
            return None

        action = behavior.create_action(
            goal
        )

        return Plan(
            goal=goal,
            actions=[action]
        )