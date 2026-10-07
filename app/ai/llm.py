import os
from abc import ABC, abstractmethod
from pathlib import Path

from dotenv import load_dotenv

from .context import AIContext
from .prompts import SYSTEM_PROMPT, build_chat_prompt


# ---------------------------------------------------------
# Загрузка .env
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(ENV_FILE)


# ---------------------------------------------------------
# Базовый интерфейс LLM
# ---------------------------------------------------------

class LLM(ABC):

    @abstractmethod
    def generate(self, context: AIContext) -> str:
        raise NotImplementedError


# ---------------------------------------------------------
# Тестовая нейронка
# ---------------------------------------------------------

class MockLLM(LLM):

    def generate(self, context: AIContext) -> str:

        if context.user_message:
            return (
                "Я получил твоё сообщение: "
                + context.user_message
            )

        return "Я пока не знаю, что ответить."


# ---------------------------------------------------------
# OpenAI
# ---------------------------------------------------------

class OpenAILLM(LLM):

    def __init__(
        self,
        model: str | None = None
    ):
        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise RuntimeError(
                "Не найден OPENAI_API_KEY.\n\n"
                "Создай файл .env в корне проекта:\n\n"
                "OPENAI_API_KEY=твой_ключ\n"
                "OPENAI_MODEL=gpt-6-luna\n"
            )

        try:
            from openai import OpenAI
        except ImportError as error:
            raise RuntimeError(
                "Пакет openai не установлен.\n"
                "Установи его командой:\n\n"
                "pip install openai"
            ) from error

        self.client = OpenAI(
            api_key=api_key
        )

        self.model = (
            model
            or os.getenv(
                "OPENAI_MODEL",
                "gpt-6-luna"
            )
        )

    def generate(
        self,
        context: AIContext
    ) -> str:

        development = context.system_data.get(
            "personality_changes",
            []
        )

        development_context = "\n".join(
            f"- {change}"
            for change in development
        )

        prompt = build_chat_prompt(
            character_context=context.build_character_context(),
            memory_context=context.build_memory_context(),
            conversation_context=context.build_conversation_context(),
            development_context=development_context,
            message=context.user_message or ""
        )

        try:
            response = self.client.responses.create(
                model=self.model,
                instructions=SYSTEM_PROMPT,
                input=prompt
            )

        except Exception as error:
            raise RuntimeError(
                f"Ошибка обращения к OpenAI API: {error}"
            ) from error

        return response.output_text