from .actions import Action, ActionType
from .goals import Goal, GoalType
from .character import Character


class Behavior:
    def __init__(self, character: Character):
        self.character = character

    def evaluate(self) -> Goal | None:
        needs = self.character.needs

        if needs.energy < 20:
            return Goal(
                type=GoalType.SLEEP,
                priority=100.0,
                description="Восстановить энергию"
            )

        if needs.hunger < 20:
            return Goal(
                type=GoalType.EAT,
                priority=90.0,
                description="Утолить голод"
            )

        if needs.hygiene < 20:
            return Goal(
                type=GoalType.WASH,
                priority=80.0,
                description="Восстановить гигиену"
            )

        if needs.social < 20:
            return Goal(
                type=GoalType.SOCIALIZE,
                priority=70.0,
                description="Пообщаться с кем-нибудь"
            )

        if needs.fun < 20:
            return Goal(
                type=GoalType.HAVE_FUN,
                priority=60.0,
                description="Развлечься"
            )

        if needs.comfort < 20:
            return Goal(
                type=GoalType.RELAX,
                priority=50.0,
                description="Отдохнуть и повысить комфорт"
            )

        return None

    def create_action(self, goal: Goal) -> Action:
        actions = {
            GoalType.SLEEP: ActionType.SLEEP,
            GoalType.EAT: ActionType.EAT,
            GoalType.WASH: ActionType.WASH,
            GoalType.SOCIALIZE: ActionType.TALK,
            GoalType.HAVE_FUN: ActionType.PLAY,
            GoalType.RELAX: ActionType.RELAX,
            GoalType.EXPLORE: ActionType.EXPLORE,
            GoalType.BUILD: ActionType.BUILD,
            GoalType.TALK: ActionType.TALK,
        }

        action_type = actions.get(goal.type, ActionType.IDLE)

        return Action(
            type=action_type,
            target_id=goal.target_id
        )

    def update(self) -> Action | None:
        goal = self.evaluate()

        if goal is None:
            return None

        return self.create_action(goal)