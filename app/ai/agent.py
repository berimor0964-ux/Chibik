from typing import Callable

from app.character.character import Character
from app.character.behavior import Behavior
from app.character.memory import (
    MemoryStore,
    MemoryType
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
        ] | None = None
    ):

        self.character = character

        self.llm = llm

        self.planner = planner

        self.memory = (
            memory
            or character.memory
        )

        self.behavior = Behavior(
            character
        )

        self.conversation_history = []

        # -----------------------------------------------------
        # Persistence callbacks
        # -----------------------------------------------------

        self.interaction_saver = (
            interaction_saver
        )

        self.memory_saver = (
            memory_saver
        )

        self.character_saver = (
            character_saver
        )

    # =========================================================
    # THINK
    # =========================================================

    def think(
        self,
        context: AIContext
    ):

        return self.planner.plan(
            character=self.character,
            context=context
        )

    # =========================================================
    # CHAT
    # =========================================================

    def chat(
        self,
        message: str
    ) -> str:

        # -----------------------------------------------------
        # 1. Save user message in short-term memory
        # -----------------------------------------------------

        user_memory = self.memory.remember(
            content=message,
            memory_type=MemoryType.SHORT_TERM,
            importance=30.0,
            metadata={
                "type": "user_message"
            }
        )

        if self.memory_saver:
            self.memory_saver(
                user_memory
            )

        # -----------------------------------------------------
        # 2. Add to conversation
        # -----------------------------------------------------

        self.conversation_history.append({
            "role": "user",
            "content": message
        })

        # -----------------------------------------------------
        # 3. Develop personality
        # -----------------------------------------------------

        changes = (
            self.character
            .personality
            .develop_from_message(
                message
            )
        )

        # -----------------------------------------------------
        # 4. Search memories
        # -----------------------------------------------------

        memories = (
            self.memory
            .get_recent(
                limit=20
            )
        )

        important_memories = (
            self.memory
            .get_important(
                minimum_importance=70.0
            )
        )

        # Combine without duplicates
        all_memories = []

        for memory in (
            important_memories
            + memories
        ):

            if memory not in all_memories:

                all_memories.append(
                    memory
                )

        # -----------------------------------------------------
        # 5. Build context
        # -----------------------------------------------------

        context = AIContext(
            character=self.character,
            user_message=message,
            memories=all_memories,
            conversation_history=(
                self.conversation_history.copy()
            )
        )

        # -----------------------------------------------------
        # 6. Tell AI about development
        # -----------------------------------------------------

        if changes:

            context.add_system_data(
                "personality_changes",
                changes
            )

        # -----------------------------------------------------
        # 7. Generate response
        # -----------------------------------------------------

        response = self.llm.generate(
            context=context
        )

        # -----------------------------------------------------
        # 8. Save assistant response
        # -----------------------------------------------------

        assistant_memory = (
            self.memory.remember(
                content=response,
                memory_type=MemoryType.SHORT_TERM,
                importance=30.0,
                metadata={
                    "type": "assistant_message"
                }
            )
        )

        if self.memory_saver:

            self.memory_saver(
                assistant_memory
            )

        # -----------------------------------------------------
        # 9. Save episodic interaction
        # -----------------------------------------------------

        interaction_memory = (
            self.memory
            .remember_interaction(
                user_message=message,
                assistant_message=response
            )
        )

        if self.memory_saver:

            self.memory_saver(
                interaction_memory
            )

        # -----------------------------------------------------
        # 10. Conversation history
        # -----------------------------------------------------

        self.conversation_history.append({
            "role": "assistant",
            "content": response
        })

        # -----------------------------------------------------
        # 11. Save interaction
        # -----------------------------------------------------

        if self.interaction_saver:

            self.interaction_saver(
                message,
                response
            )

        # -----------------------------------------------------
        # 12. Save changed personality
        # -----------------------------------------------------

        if changes and self.character_saver:

            self.character_saver(
                self.character
            )

        return response

    # =========================================================
    # UPDATE
    # =========================================================

    def update(self):

        return self.behavior.update()