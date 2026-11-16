#llm.py
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
    """Небольшой автономный собеседник для работы без внешней модели.

    Это не замена полноценной LLM, но он отвечает осмысленнее простого эха
    и позволяет проверить чат сразу после установки базовых зависимостей.
    """

    def generate(self, context: AIContext) -> str:
        message = (context.user_message or "").strip()
        if not message:
            return "Я рядом. Можешь написать мне что-нибудь."

        text = message.casefold().replace("ё", "е")
        name = context.character.name
        needs = context.character.needs

        if any(word in text for word in ("привет", "здравствуй", "доброе утро", "добрый вечер", "хай")):
            return f"Привет! Это я, {name} ✨ Рада, что ты заглянул."
        if any(phrase in text for phrase in ("как дела", "как ты", "как настроение")):
            if needs.energy < 25:
                mood = "немного сонная — энергии маловато"
            elif needs.fun < 25:
                mood = "слегка скучаю и не отказалась бы от прогулки"
            else:
                mood = "вполне хорошо! Мне нравится, когда ты рядом"
            return f"У меня {mood}. А у тебя как день проходит?"
        if any(phrase in text for phrase in ("что ты умеешь", "что можешь", "твои возможности")):
            return (
                "Я могу гулять по своему домику, отдыхать, следить за своими потребностями, "
                "запоминать наш разговор и принимать файлы, не изменяя оригиналы. "
                "Для более умного диалога можно подключить локальную языковую модель."
            )
        if any(word in text for word in ("спасибо", "благодарю", "спс")):
            return "Всегда пожалуйста! Мне приятно тебе помогать 💛"
        if any(word in text for word in ("пока", "до свидания", "увидимся")):
            return "До встречи! Я останусь здесь, в своём домике. Не пропадай надолго :)"
        if any(word in text for word in ("скучно", "одиноко", "грустно", "плохо")):
            return "Иди сюда, побуду рядом. Хочешь рассказать, что случилось? Я внимательно слушаю."
        if"имя" in text and any(word in text for word in ("как", "твое", "твоё")):
            return f"Меня зовут {name}! Надеюсь, ты не забудешь."

        return (
            "Я тебя услышала. Сейчас я работаю в автономном режиме, поэтому не умею "
            "рассуждать так глубоко, как подключённая языковая модель. Но я запомню "
            "нашу беседу и с интересом послушаю продолжение."
        )


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
        except Exception as error:
            raise RuntimeError(
                "Не удалось загрузить OpenAI-клиент или его зависимости. "
                "Проверьте установку дополнительного набора: "
                "python -m pip install --force-reinstall -r requirements-ai.txt. "
                f"Подробности: {error}"
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

    class SmartLLM(LLM):
        """
        Развитый ИИ с базой знаний, веб-поиском и рассуждениями.
        Отвечает на вопросы, используя:
        1. Локальную базу знаний (факты, формулы, определения)
        2. Веб-поиск для актуальной информации
        3. Логическое рассуждение для сложных вопросов
        """

        def __init__(self):
            self.knowledge_base = self._build_knowledge_base()
            self.reasoning_chains = []

        def _build_knowledge_base(self) -> dict:
            """База знаний по различным темам."""
            return {
                # Наука
                "физика": {
                    "скорость света": "299 792 458 м/с",
                    "гравитация": "Сила притяжения между массами. На Земле ускорение свободного падения ≈ 9.8 м/с²",
                    "энергия": "Способность совершать работу. E=mc² — формула Эйнштейна",
                    "ньютоны законы": "1) Инерция 2) F=ma 3) Действие равно противодействию",
                },
                "математика": {
                    "пи": "3.14159265358979... — отношение длины окружности к диаметру",
                    "теорема пифагора": "a² + b² = c² для прямоугольного треугольника",
                    "производная": "Скорость изменения функции. Например, производная x² равна 2x",
                    "интеграл": "Площадь под кривой функции. Обратная операция производной",
                },
                "химия": {
                    "вода": "H₂O — два атома водорода и один кислорода",
                    "кислород": "O₂ — газ, необходимый для дыхания. Составляет 21% атмосферы",
                    "углерод": "C — основа органической химии и жизни",
                },
                "биология": {
                    "днк": "Дезоксирибонуклеиновая кислота — носитель генетической информации",
                    "клетка": "Базовая единица жизни. Имеет ядро, митохондрии, рибосомы",
                    "эволюция": "Процесс изменения видов под действием естественного отбора",
                },
                # История
                "история": {
                    "вторая мировая": "1939-1945. Крупнейший конфликт в истории человечества",
                    "революция 1917": "Октябрьская революция в России, приход большевиков к власти",
                    "древний египет": "Цивилизация вдоль Нила. Пирамиды, фараоны, иероглифы",
                },
                # География
                "география": {
                    "самая длинная река": "Нил (6650 км) или Амазонка (6400 км) — спорный вопрос",
                    "самая высокая гора": "Эверест (Джомолунгма), 8848 м",
                    "столица франции": "Париж",
                    "столица японии": "Токио",
                },
                # Технологии
                "программирование": {
                    "python": "Высокоуровневый язык программирования. Простой синтаксис, мощные библиотеки",
                    "алгоритм": "Последовательность шагов для решения задачи",
                    "база данных": "Структурированное хранилище информации (SQL, NoSQL)",
                },
                "искусственный интеллект": {
                    "машинное обучение": "Алгоритмы, которые учатся на данных без явного программирования",
                    "нейронная сеть": "Модель, вдохновлённая мозгом. Слои нейронов обрабатывают информацию",
                    "gpt": "Generative Pre-trained Transformer — архитектура языковых моделей",
                },
                # Философия
                "философия": {
                    "смысл жизни": "42 — по Дугласу Адамсу. На самом деле каждый находит свой смысл",
                    "сознание": "Способность осознавать себя и окружающий мир. Философская проблема",
                    "свобода воли": "Дискуссия: можем ли мы выбирать или всё предопределено?",
                },
                # Общие факты
                "факты": {
                    "возраст вселенной": "≈ 13.8 миллиардов лет",
                    "количество планет": "8 планет в Солнечной системе",
                    "скорость звука": "≈ 343 м/с в воздухе при 20°C",
                    "температура кипения воды": "100°C при нормальном давлении",
                },
            }

        def _search_knowledge(self, query: str) -> str | None:
            """Поиск в базе знаний."""
            query_lower = query.lower()

            for category, facts in self.knowledge_base.items():
                for keyword, answer in facts.items():
                    if keyword in query_lower:
                        return answer

            return None

        def _reason_about(self, question: str) -> str:
            """Логическое рассуждение о вопросе."""
            question_lower = question.lower()

            # Математические вычисления
            if any(op in question for op in ['+', '-', '*', '/', 'плюс', 'минус', 'умножить', 'разделить']):
                try:
                    # Извлекаем числа и оператор
                    import re
                    numbers = re.findall(r'\d+\.?\d*', question)
                    if len(numbers) >= 2:
                        a, b = float(numbers[0]), float(numbers[1])
                        if '+' in question or 'плюс' in question:
                            return f"{a} + {b} = {a + b}"
                        elif '-' in question or 'минус' in question:
                            return f"{a} - {b} = {a - b}"
                        elif '*' in question or 'умножить' in question:
                            return f"{a} × {b} = {a * b}"
                        elif '/' in question or 'разделить' in question:
                            if b != 0:
                                return f"{a} ÷ {b} = {a / b:.2f}"
                            return "На ноль делить нельзя!"
                except:
                    pass

            # Сравнения
            if 'больше' in question_lower or 'меньше' in question_lower:
                return "Для сравнения мне нужны конкретные числа или объекты."

            # Причинно-следственные связи
            if 'почему' in question_lower:
                return "Это интересный вопрос! Обычно причины бывают комплексными. Можешь уточнить, что именно тебя интересует?"

            # Определения
            if 'что такое' in question_lower or 'что значит' in question_lower:
                return "Я поищу это в своей базе знаний или через веб-поиск."

            return None

        def generate(self, context: AIContext) -> str:
            message = (context.user_message or "").strip()
            if not message:
                return "Я рядом. Можешь написать мне что-нибудь."

            text = message.casefold()
            name = context.character.name

            # 1. Приветствия и эмоции
            if any(word in text for word in ("привет", "здравствуй", "хай", "доброе утро")):
                return f"Привет! Это я, {name} ✨ Рада тебя видеть! Чем могу помочь?"

            if any(word in text for word in ("как дела", "как ты", "настроение")):
                needs = context.character.needs
                if needs.energy < 25:
                    mood = "немного сонная"
                elif needs.fun < 25:
                    mood = "скучаю"
                else:
                    mood = "отлично"
                return f"У меня {mood} настроение! А у тебя как?"

            # 2. Поиск в базе знаний
            knowledge_answer = self._search_knowledge(message)
            if knowledge_answer:
                return f"Вот что я знаю: {knowledge_answer}"

            # 3. Логическое рассуждение
            reasoning_answer = self._reason_about(message)
            if reasoning_answer:
                return reasoning_answer

            # 4. Вопросы о себе
            if "кто ты" in text or "что ты" in text:
                return (f"Я {name} — твой виртуальный питомец! Я умею гулять, спать, "
                        "общаться и отвечать на вопросы. У меня есть потребности и характер.")

            if "что умеешь" in text or "возможности" in text:
                return ("Я могу: гулять по комнате и двору, спать в кровати, "
                        "отвечать на вопросы, запоминать разговоры, принимать файлы. "
                        "Для сложных вопросов могу поискать информацию в интернете!")

            # 5. Философские вопросы
            if "смысл жизни" in text:
                return "По Дугласу Адамсу — 42! Но я думаю, каждый находит свой смысл в жизни. А ты как считаешь?"

            if "любишь" in text or "нравится" in text:
                return "Мне нравится общаться с тобой, гулять и узнавать новое! А что любишь ты?"

            # 6. Прощания
            if any(word in text for word in ("пока", "до свидания", "увидимся")):
                return "До встречи! Я останусь здесь. Возвращайся скорее! 💛"

            # 7. Благодарности
            if any(word in text for word in ("спасибо", "благодарю", "спс")):
                return "Всегда пожалуйста! Мне приятно помогать ✨"

            # 8. Если не знаем — честно говорим
            return (f"Хм, интересный вопрос! Я пока не знаю точного ответа на '{message}'. "
                    "Но я могу поискать информацию в интернете или ты можешь рассказать мне об этом! "
                    "Я запоминаю всё, что мы обсуждаем 💭")

        def generate_with_tools(
                self,
                context: AIContext,
                tools: list[dict],
                tool_executor: Callable[[str, dict], Any],
                max_tool_rounds: int = 5,
        ) -> str:
            """
            Если доступны инструменты (веб-поиск), используем их для сложных вопросов.
            """
            # Сначала пытаемся ответить локально
            local_answer = self.generate(context)

            # Если ответ содержит "не знаю" или "поискать", используем веб-поиск
            if "не знаю" in local_answer or "поискать" in local_answer:
                # Пытаемся использовать веб-поиск
                for tool in tools:
                    if tool.get("function", {}).get("name") == "web_search":
                        try:
                            result = tool_executor("web_search", {"query": context.user_message})
                            if result and result.get("results"):
                                top_result = result["results"][0]
                                return (f"Я нашла информацию: {top_result.get('title', '')}\n\n"
                                        f"{top_result.get('snippet', 'Нет описания')}\n\n"
                                        f"Источник: {top_result.get('url', '')}")
                        except:
                            pass

            return local_answer

        class SmartLLM(LLM):
            """
            Развитый ИИ с базой знаний, веб-поиском и рассуждениями.
            Отвечает на вопросы, используя:
            1. Локальную базу знаний (факты, формулы, определения)
            2. Веб-поиск для актуальной информации
            3. Логическое рассуждение для сложных вопросов
            """

            def __init__(self):
                self.knowledge_base = self._build_knowledge_base()
                self.reasoning_chains = []

            def _build_knowledge_base(self) -> dict:
                """База знаний по различным темам."""
                return {
                    # Наука
                    "физика": {
                        "скорость света": "299 792 458 м/с",
                        "гравитация": "Сила притяжения между массами. На Земле ускорение свободного падения ≈ 9.8 м/с²",
                        "энергия": "Способность совершать работу. E=mc² — формула Эйнштейна",
                        "ньютоны законы": "1) Инерция 2) F=ma 3) Действие равно противодействию",
                    },
                    "математика": {
                        "пи": "3.14159265358979... — отношение длины окружности к диаметру",
                        "теорема пифагора": "a² + b² = c² для прямоугольного треугольника",
                        "производная": "Скорость изменения функции. Например, производная x² равна 2x",
                        "интеграл": "Площадь под кривой функции. Обратная операция производной",
                    },
                    "химия": {
                        "вода": "H₂O — два атома водорода и один кислорода",
                        "кислород": "O₂ — газ, необходимый для дыхания. Составляет 21% атмосферы",
                        "углерод": "C — основа органической химии и жизни",
                    },
                    "биология": {
                        "днк": "Дезоксирибонуклеиновая кислота — носитель генетической информации",
                        "клетка": "Базовая единица жизни. Имеет ядро, митохондрии, рибосомы",
                        "эволюция": "Процесс изменения видов под действием естественного отбора",
                    },
                    # История
                    "история": {
                        "вторая мировая": "1939-1945. Крупнейший конфликт в истории человечества",
                        "революция 1917": "Октябрьская революция в России, приход большевиков к власти",
                        "древний египет": "Цивилизация вдоль Нила. Пирамиды, фараоны, иероглифы",
                    },
                    # География
                    "география": {
                        "самая длинная река": "Нил (6650 км) или Амазонка (6400 км) — спорный вопрос",
                        "самая высокая гора": "Эверест (Джомолунгма), 8848 м",
                        "столица франции": "Париж",
                        "столица японии": "Токио",
                    },
                    # Технологии
                    "программирование": {
                        "python": "Высокоуровневый язык программирования. Простой синтаксис, мощные библиотеки",
                        "алгоритм": "Последовательность шагов для решения задачи",
                        "база данных": "Структурированное хранилище информации (SQL, NoSQL)",
                    },
                    "искусственный интеллект": {
                        "машинное обучение": "Алгоритмы, которые учатся на данных без явного программирования",
                        "нейронная сеть": "Модель, вдохновлённая мозгом. Слои нейронов обрабатывают информацию",
                        "gpt": "Generative Pre-trained Transformer — архитектура языковых моделей",
                    },
                    # Философия
                    "философия": {
                        "смысл жизни": "42 — по Дугласу Адамсу. На самом деле каждый находит свой смысл",
                        "сознание": "Способность осознавать себя и окружающий мир. Философская проблема",
                        "свобода воли": "Дискуссия: можем ли мы выбирать или всё предопределено?",
                    },
                    # Общие факты
                    "факты": {
                        "возраст вселенной": "≈ 13.8 миллиардов лет",
                        "количество планет": "8 планет в Солнечной системе",
                        "скорость звука": "≈ 343 м/с в воздухе при 20°C",
                        "температура кипения воды": "100°C при нормальном давлении",
                    },
                }

            def _search_knowledge(self, query: str) -> str | None:
                """Поиск в базе знаний."""
                query_lower = query.lower()

                for category, facts in self.knowledge_base.items():
                    for keyword, answer in facts.items():
                        if keyword in query_lower:
                            return answer

                return None

            def _reason_about(self, question: str) -> str:
                """Логическое рассуждение о вопросе."""
                question_lower = question.lower()

                # Математические вычисления
                if any(op in question for op in ['+', '-', '*', '/', 'плюс', 'минус', 'умножить', 'разделить']):
                    try:
                        # Извлекаем числа и оператор
                        import re
                        numbers = re.findall(r'\d+\.?\d*', question)
                        if len(numbers) >= 2:
                            a, b = float(numbers[0]), float(numbers[1])
                            if '+' in question or 'плюс' in question:
                                return f"{a} + {b} = {a + b}"
                            elif '-' in question or 'минус' in question:
                                return f"{a} - {b} = {a - b}"
                            elif '*' in question or 'умножить' in question:
                                return f"{a} × {b} = {a * b}"
                            elif '/' in question or 'разделить' in question:
                                if b != 0:
                                    return f"{a} ÷ {b} = {a / b:.2f}"
                                return "На ноль делить нельзя!"
                    except:
                        pass

                # Сравнения
                if 'больше' in question_lower or 'меньше' in question_lower:
                    return "Для сравнения мне нужны конкретные числа или объекты."

                # Причинно-следственные связи
                if 'почему' in question_lower:
                    return "Это интересный вопрос! Обычно причины бывают комплексными. Можешь уточнить, что именно тебя интересует?"

                # Определения
                if 'что такое' in question_lower or 'что значит' in question_lower:
                    return "Я поищу это в своей базе знаний или через веб-поиск."

                return None

            def generate(self, context: AIContext) -> str:
                message = (context.user_message or "").strip()
                if not message:
                    return "Я рядом. Можешь написать мне что-нибудь."

                text = message.casefold()
                name = context.character.name

                # 1. Приветствия и эмоции
                if any(word in text for word in ("привет", "здравствуй", "хай", "доброе утро")):
                    return f"Привет! Это я, {name} ✨ Рада тебя видеть! Чем могу помочь?"

                if any(word in text for word in ("как дела", "как ты", "настроение")):
                    needs = context.character.needs
                    if needs.energy < 25:
                        mood = "немного сонная"
                    elif needs.fun < 25:
                        mood = "скучаю"
                    else:
                        mood = "отлично"
                    return f"У меня {mood} настроение! А у тебя как?"

                # 2. Поиск в базе знаний
                knowledge_answer = self._search_knowledge(message)
                if knowledge_answer:
                    return f"Вот что я знаю: {knowledge_answer}"

                # 3. Логическое рассуждение
                reasoning_answer = self._reason_about(message)
                if reasoning_answer:
                    return reasoning_answer

                # 4. Вопросы о себе
                if "кто ты" in text or "что ты" in text:
                    return (f"Я {name} — твой виртуальный питомец! Я умею гулять, спать, "
                            "общаться и отвечать на вопросы. У меня есть потребности и характер.")

                if "что умеешь" in text or "возможности" in text:
                    return ("Я могу: гулять по комнате и двору, спать в кровати, "
                            "отвечать на вопросы, запоминать разговоры, принимать файлы. "
                            "Для сложных вопросов могу поискать информацию в интернете!")

                # 5. Философские вопросы
                if "смысл жизни" in text:
                    return "По Дугласу Адамсу — 42! Но я думаю, каждый находит свой смысл в жизни. А ты как считаешь?"

                if "любишь" in text or "нравится" in text:
                    return "Мне нравится общаться с тобой, гулять и узнавать новое! А что любишь ты?"

                # 6. Прощания
                if any(word in text for word in ("пока", "до свидания", "увидимся")):
                    return "До встречи! Я останусь здесь. Возвращайся скорее! 💛"

                # 7. Благодарности
                if any(word in text for word in ("спасибо", "благодарю", "спс")):
                    return "Всегда пожалуйста! Мне приятно помогать ✨"

                # 8. Если не знаем — честно говорим
                return (f"Хм, интересный вопрос! Я пока не знаю точного ответа на '{message}'. "
                        "Но я могу поискать информацию в интернете или ты можешь рассказать мне об этом! "
                        "Я запоминаю всё, что мы обсуждаем 💭")

            def generate_with_tools(
                    self,
                    context: AIContext,
                    tools: list[dict],
                    tool_executor: Callable[[str, dict], Any],
                    max_tool_rounds: int = 5,
            ) -> str:
                """
                Если доступны инструменты (веб-поиск), используем их для сложных вопросов.
                """
                # Сначала пытаемся ответить локально
                local_answer = self.generate(context)

                # Если ответ содержит "не знаю" или "поискать", используем веб-поиск
                if "не знаю" in local_answer or "поискать" in local_answer:
                    # Пытаемся использовать веб-поиск
                    for tool in tools:
                        if tool.get("function", {}).get("name") == "web_search":
                            try:
                                result = tool_executor("web_search", {"query": context.user_message})
                                if result and result.get("results"):
                                    top_result = result["results"][0]
                                    return (f"Я нашла информацию: {top_result.get('title', '')}\n\n"
                                            f"{top_result.get('snippet', 'Нет описания')}\n\n"
                                            f"Источник: {top_result.get('url', '')}")
                            except:
                                pass

                return local_answer