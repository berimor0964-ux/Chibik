from abc import ABC, abstractmethod
from typing import Any


class AITool(ABC):

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def description(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def execute(self, **kwargs: Any) -> Any:
        raise NotImplementedError


class FindObjectTool(AITool):

    @property
    def name(self) -> str:
        return "find_object"

    @property
    def description(self) -> str:
        return "Найти объект в виртуальном мире."

    def execute(
        self,
        world,
        object_type: str
    ) -> Any:
        return world.find_object(object_type)


class MoveToTool(AITool):

    @property
    def name(self) -> str:
        return "move_to"

    @property
    def description(self) -> str:
        return "Переместить персонажа к указанной позиции."

    def execute(
        self,
        world,
        start,
        target
    ) -> Any:
        return world.find_path(
            start,
            target
        )


class BuildObjectTool(AITool):

    @property
    def name(self) -> str:
        return "build_object"

    @property
    def description(self) -> str:
        return "Создать объект в виртуальном мире."

    def execute(
        self,
        world,
        object_type: str,
        position
    ) -> Any:
        if not world.can_build(
            object_type,
            position
        ):
            return None

        return world.spawn_object(
            object_type,
            position
        )


class TalkToCharacterTool(AITool):

    @property
    def name(self) -> str:
        return "talk_to_character"

    @property
    def description(self) -> str:
        return "Начать взаимодействие с другим персонажем."

    def execute(
        self,
        character_id: str
    ) -> dict[str, str]:
        return {
            "character_id": character_id,
            "status": "requested"
        }


class AIToolRegistry:

    def __init__(self):
        self._tools: dict[str, AITool] = {}

    def register(self, tool: AITool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> AITool | None:
        return self._tools.get(name)

    def get_all(self) -> list[AITool]:
        return list(self._tools.values())

    def execute(
        self,
        name: str,
        **kwargs: Any
    ) -> Any:
        tool = self.get(name)

        if tool is None:
            raise ValueError(
                f"AI tool not found: {name}"
            )

        return tool.execute(**kwargs)