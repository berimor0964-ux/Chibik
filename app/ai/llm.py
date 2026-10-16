import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable

from dotenv import load_dotenv

from .context import AIContext
from .prompts import SYSTEM_PROMPT, build_chat_prompt


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(ENV_FILE)


class LLM(ABC):

    @abstractmethod
    def generate(self, context: AIContext) -> str:
        raise NotImplementedError

    def generate_with_tools(
        self,
        context: AIContext,
        tools: list[dict],
        tool_executor: Callable[[str, dict], Any],
        max_tool_rounds: int = 5,
    ) -> str:
        """
        Совместимый запасной вариант для LLM,
        которые пока не поддерживают вызовы инструментов.
        """
        return self.generate(context)


class MockLLM(LLM):

    def generate(self, context: AIContext) -> str:
        if context.user_message:
            return (
                "Я получил твоё сообщение: "
                + context.user_message
            )

        return "Я пока не знаю, что ответить."


class LocalLLM(LLM):

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
    ):
        self.base_url = (
            base_url
            or os.getenv(
                "LOCAL_LLM_URL",
                "http://127.0.0.1:8080/v1",
            )
        )

        self.model = (
            model
            or os.getenv(
                "LOCAL_LLM_MODEL",
                "Qwen3-8B-Q4_K_M",
            )
        )

        try:
            from openai import OpenAI
        except ImportError as error:
            raise RuntimeError(
                "Не установлен пакет openai.\n\n"
                "Установи:\n"
                "pip install openai"
            ) from error

        self.client = OpenAI(
            base_url=self.base_url,
            api_key="local",
        )

    def _build_prompt(self, context: AIContext) -> str:
        development = context.system_data.get(
            "personality_changes",
            [],
        )

        development_context = "\n".join(
            f"- {change}"
            for change in development
        )

        return build_chat_prompt(
            character_context=context.build_character_context(),
            memory_context=context.build_memory_context(),
            conversation_context=context.build_conversation_context(),
            development_context=development_context,
            message=context.user_message or "",
        )

    def _messages(self, context: AIContext) -> list[dict]:
        return [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": self._build_prompt(context),
            },
        ]

    def _request(self, **kwargs):
        try:
            return self.client.chat.completions.create(
                model=self.model,
                extra_body={
                    "chat_template_kwargs": {
                        "enable_thinking": False,
                    },
                },
                **kwargs,
            )
        except Exception as error:
            raise RuntimeError(
                "Ошибка локальной Qwen3:\n"
                f"{error}"
            ) from error

    def generate(self, context: AIContext) -> str:
        response = self._request(
            messages=self._messages(context),
            temperature=0.8,
            top_p=0.9,
            max_tokens=1024,
        )

        content = response.choices[0].message.content

        if not content:
            return "..."

        return content.strip()

    def generate_with_tools(
        self,
        context: AIContext,
        tools: list[dict],
        tool_executor: Callable[[str, dict], Any],
        max_tool_rounds: int = 5,
    ) -> str:
        """
        Цикл вызова инструментов через OpenAI-совместимый API.

        Модель может запросить инструмент несколько раз.
        После каждого выполнения результат возвращается модели.
        """
        messages = self._messages(context)

        max_tool_rounds = max(
            1,
            min(int(max_tool_rounds), 8),
        )

        for _ in range(max_tool_rounds):
            response = self._request(
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=0.4,
                top_p=0.9,
                max_tokens=1024,
            )

            assistant_message = response.choices[0].message
            tool_calls = assistant_message.tool_calls or []

            # Если модель не запросила инструмент — это финальный ответ.
            if not tool_calls:
                content = assistant_message.content

                if not content:
                    return "Я не смогла сформировать ответ."

                return content.strip()

            # Сохраняем сообщение ассистента с вызовами инструментов.
            messages.append(
                assistant_message.model_dump(
                    exclude_none=True,
                )
            )

            for tool_call in tool_calls:
                tool_name = tool_call.function.name

                try:
                    arguments = json.loads(
                        tool_call.function.arguments or "{}"
                    )

                    if not isinstance(arguments, dict):
                        raise ValueError(
                            "Аргументы инструмента должны быть JSON-объектом."
                        )

                    result = tool_executor(
                        tool_name,
                        arguments,
                    )

                    result_content = json.dumps(
                        {
                            "success": True,
                            "result": result,
                        },
                        ensure_ascii=False,
                        default=str,
                    )

                except Exception as error:
                    # Ошибка одного инструмента не должна обрывать весь диалог.
                    result_content = json.dumps(
                        {
                            "success": False,
                            "error": str(error),
                        },
                        ensure_ascii=False,
                    )

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result_content,
                    }
                )

        # Лимит вызовов исчерпан. Не сообщаем, что работа выполнена,
        # если модель не вернула финальный ответ.
        messages.append(
            {
                "role": "user",
                "content": (
                    "Достигнут лимит вызовов инструментов. "
                    "Подведи итог только на основании полученных результатов. "
                    "Если задача не завершена, честно сообщи об этом."
                ),
            }
        )

        final_response = self._request(
            messages=messages,
            temperature=0.4,
            top_p=0.9,
            max_tokens=1024,
        )

        content = final_response.choices[0].message.content

        if not content:
            return "Не удалось получить итоговый ответ от модели."

        return content.strip()


class OpenAILLM(LLM):

    def __init__(
        self,
        model: str | None = None,
    ):
        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise RuntimeError(
                "Не найден OPENAI_API_KEY."
            )

        try:
            from openai import OpenAI
        except ImportError as error:
            raise RuntimeError(
                "Пакет openai не установлен."
            ) from error

        self.client = OpenAI(
            api_key=api_key,
        )

        self.model = (
            model
            or os.getenv("OPENAI_MODEL")
        )

        if not self.model:
            raise RuntimeError(
                "Не задана переменная OPENAI_MODEL."
            )

    def generate(self, context: AIContext) -> str:
        development = context.system_data.get(
            "personality_changes",
            [],
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
            message=context.user_message or "",
        )

        response = self.client.responses.create(
            model=self.model,
            instructions=SYSTEM_PROMPT,
            input=prompt,
        )

        return response.output_text