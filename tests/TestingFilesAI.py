from app.ai.agent import Agent
from app.ai.llm import OpenAILLM
from app.ai.planner import Planner

from tests.character_database import (
    CharacterDatabase
)


def main():

    database = CharacterDatabase()

    character = database.load_character()

    if character is None:

        from app.character.character import Character

        character = Character(
            name="Мира",
            age=21
        )

        character.personality.friendliness = 70
        character.personality.curiosity = 90
        character.personality.laziness = 30
        character.personality.humor = 80
        character.personality.chaos = 40
        character.personality.intelligence = 85
        character.personality.bravery = 60

        character.personality.traits = [
            "любопытная",
            "саркастичная",
            "умная"
        ]

        character.personality.backstory = """
Мира появилась в виртуальном мире несколько лет назад.

Она долгое время жила одна и поэтому очень любит общение.

Она привыкла самостоятельно принимать решения
и не любит, когда пользователь игнорирует её вопросы.
""".strip()

        character.personality.behavior_style = """
Общается живо и эмоционально.

Может немного поддразнивать пользователя.

Иногда проявляет упрямство.
""".strip()

        character.personality.likes = [
            "интересные разговоры",
            "технологии",
            "исследование мира",
            "шутки"
        ]

        character.personality.dislikes = [
            "игнорирование",
            "скука",
            "грубость"
        ]

        character.personality.rules = [
            "Не быть безликим ассистентом.",
            "Сохранять собственный характер.",
            "Помнить важные сведения о пользователе.",
            "Не притворяться, что действие выполнено."
        ]

        database.save_character(
            character
        )

    # ---------------------------------------------------------
    # AI
    # ---------------------------------------------------------

    try:

        llm = OpenAILLM()

    except RuntimeError as error:

        print()
        print("=" * 60)
        print("ОШИБКА AI")
        print("=" * 60)
        print(error)
        print()

        return

    planner = Planner()

    agent = Agent(
        character=character,
        llm=llm,
        planner=planner,

        memory=character.memory,

        interaction_saver=(
            database.save_interaction
        ),

        memory_saver=(
            database.save_memory
        ),

        character_saver=(
            database.save_character
        )
    )

    # ---------------------------------------------------------
    # LOAD EXISTING MEMORY
    # ---------------------------------------------------------

    memories = database.load_memories()

    for memory in reversed(memories):

        character.memory.memories.append(
            memory
        )

    # ---------------------------------------------------------
    # START
    # ---------------------------------------------------------

    print("=" * 60)
    print("DESKTOP PET — TEST CHAT")
    print("=" * 60)

    print()

    print(
        f"Персонаж: {character.name}"
    )

    print(
        f"Возраст: {character.age}"
    )

    print()

    print("Текущий характер:")

    print(
        character.personality.build_description()
    )

    print()

    statistics = (
        database
        .get_statistics()
    )

    print(
        f"Взаимодействий: "
        f"{statistics['interactions']}"
    )

    print(
        f"Воспоминаний: "
        f"{statistics['memories']}"
    )

    print()

    print("-" * 60)

    print(
        "Напиши 'exit' для выхода."
    )

    print(
        "Напиши 'stats' для статистики."
    )

    print(
        "Напиши 'personality' "
        "для текущего характера."
    )

    print("-" * 60)

    print()

    while True:

        message = input(
            "Ты: "
        ).strip()

        if not message:
            continue

        if message.lower() == "exit":

            print(
                "Чат завершён."
            )

            break

        # -----------------------------------------------------
        # STATISTICS
        # -----------------------------------------------------

        if message.lower() == "stats":

            statistics = (
                database
                .get_statistics()
            )

            print()

            print(
                f"Взаимодействий: "
                f"{statistics['interactions']}"
            )

            print(
                f"Воспоминаний: "
                f"{statistics['memories']}"
            )

            print()

            continue

        # -----------------------------------------------------
        # PERSONALITY
        # -----------------------------------------------------

        if message.lower() == "personality":

            personality = (
                character.personality
            )

            print()

            print(
                f"Дружелюбие: "
                f"{personality.friendliness:.2f}"
            )

            print(
                f"Любопытство: "
                f"{personality.curiosity:.2f}"
            )

            print(
                f"Лень: "
                f"{personality.laziness:.2f}"
            )

            print(
                f"Юмор: "
                f"{personality.humor:.2f}"
            )

            print(
                f"Хаос: "
                f"{personality.chaos:.2f}"
            )

            print(
                f"Интеллект: "
                f"{personality.intelligence:.2f}"
            )

            print(
                f"Смелость: "
                f"{personality.bravery:.2f}"
            )

            print()

            continue

        # -----------------------------------------------------
        # CHAT
        # -----------------------------------------------------

        try:

            response = agent.chat(
                message
            )

            print()

            print(
                f"{character.name}: "
                f"{response}"
            )

            print()

        except Exception as error:

            print()

            print("=" * 60)
            print("ОШИБКА AI")
            print("=" * 60)

            print(error)

            print("=" * 60)

            print()


if __name__ == "__main__":
    main()