# agent.py
import json
from typing import Callable

from .web_tools import (
    WebSearchTool,
    EdgeSearchTool,
    BrowserManager,
    BrowserOpenTool,
    BrowserReadTool,
    BrowserTypeTool,
    BrowserClickTool,
)

from app.character.character import Character
from app.character.behavior import Behavior
from app.character.memory import (
    MemoryStore,
    MemoryType,
)

from .context import AIContext
from .llm import LLM
from .planner import Planner


class Agent:

    def __init__(
        self,
        character: Character,
        llm: LLM,
        planner: Planner,
        memory: MemoryStore | None = None,
        interaction_saver: Callable[
            [str, str],
            None
        ] | None = None,
        memory_saver: Callable[
            [object],
            None
        ] | None = None,
        character_saver: Callable[
            [Character],
            None
        ] | None = None,

    ):
        self.character = character
        self.llm = llm
        self.planner = planner

        self.memory = memory or character.memory
        self.behavior = Behavior(character)

        self.conversation_history: list[dict[str, str]] = []

        self.interaction_saver = interaction_saver
        self.memory_saver = memory_saver
        self.character_saver = character_saver

        # Отдельный профиль браузера Desktop Pet.
        self.browser = BrowserManager()

        self.tools = {
            "web_search": WebSearchTool(),
            "edge_search": EdgeSearchTool(),
            "browser_open": BrowserOpenTool(self.browser),
            "browser_read": BrowserReadTool(self.browser),
            "browser_type": BrowserTypeTool(self.browser),
            "browser_click": BrowserClickTool(self.browser),
        }

    def execute_tool(self, name: str, **kwargs):
        """Выполнить зарегистрированный инструмент."""
        tool = self.tools.get(name)

        if tool is None:
            raise ValueError(
                f"Неизвестный инструмент: {name}"
            )

        return tool.execute(**kwargs)

    def _execute_tool_call(
            self,
            name: str,
            arguments: dict,
    ):
        """
        Выполнить вызов модели.

        Инструменты вызываются только из белого списка self.tools.
        """
        if name not in self.tools:
            raise ValueError(
                f"Модели запрещено вызывать инструмент: {name}"
            )

        if not isinstance(arguments, dict):
            raise ValueError(
                "Аргументы инструмента должны быть объектом."
            )

        return self.execute_tool(
            name,
            **arguments,
        )

    def _tool_schemas(self):
        return [
            tool.to_openai_tool()
            for tool in self.tools.values()
        ]

    def think(
        self,
        context: AIContext
    ):
        return self.planner.plan(
            character=self.character,
            context=context
        )

    def chat(
        self,
        message: str
    ) -> str:

        user_memory = self.memory.remember(
            content=message,
            memory_type=MemoryType.SHORT_TERM,
            importance=30.0,
            metadata={
                "type": "user_message"
            }
        )

        if self.memory_saver:
            self.memory_saver(user_memory)

        self.conversation_history.append(
            {
                "role": "user",
                "content": message
            }
        )

        changes = (
            self.character
            .personality
            .develop_from_message(message)
        )

        memories = self.memory.get_recent(
            limit=20
        )

        important_memories = self.memory.get_important(
            minimum_importance=70.0
        )

        all_memories = []

        for memory in important_memories + memories:
            if memory not in all_memories:
                all_memories.append(memory)

        context = AIContext(
            character=self.character,
            user_message=message,
            memories=all_memories,
            conversation_history=(
                self.conversation_history.copy()
            )
        )

        if changes:
            context.add_system_data(
                "personality_changes",
                changes
            )

        # Если LLM поддерживает инструменты, модель сможет сама
        # запросить поиск, открытие сайта, чтение и другие действия.
        response = self.llm.generate_with_tools(
            context=context,
            tools=self._tool_schemas(),
            tool_executor=self._execute_tool_call,
            max_tool_rounds=5,
        )

        assistant_memory = self.memory.remember(
            content=response,
            memory_type=MemoryType.SHORT_TERM,
            importance=30.0,
            metadata={
                "type": "assistant_message"
            }
        )

        if self.memory_saver:
            self.memory_saver(assistant_memory)

        interaction_memory = self.memory.remember_interaction(
            user_message=message,
            assistant_message=response
        )

        if self.memory_saver:
            self.memory_saver(interaction_memory)

        self.conversation_history.append(
            {
                "role": "assistant",
                "content": response
            }
        )

        if self.interaction_saver:
            self.interaction_saver(
                message,
                response
            )

        if changes and self.character_saver:
            self.character_saver(self.character)

        return response

    def update(self):
        return self.behavior.update()

    def close(self):
        """Закрыть браузер и освободить ресурсы."""
        self.browser.close()