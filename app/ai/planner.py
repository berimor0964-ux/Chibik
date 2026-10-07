from dataclasses import dataclass

from app.character.actions import Action
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

        goal = character_behavior_goal(character)

        if goal is None:
            return None

        action = create_action_for_goal(goal)

        return Plan(
            goal=goal,
            actions=[action]
        )


def character_behavior_goal(
    character: Character
) -> Goal | None:

    from app.character.behavior import Behavior

    behavior = Behavior(character)

    return behavior.evaluate()


def create_action_for_goal(goal: Goal) -> Action:
    from app.character.behavior import Behavior

    from app.character.character import Character

    temporary_character = Character(
        name="planner",
        age=0
    )

    behavior = Behavior(temporary_character)

    return behavior.create_action(goal)