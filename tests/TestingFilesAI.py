from app.ai.agent import Agent
from app.ai.llm import LocalLLM
from app.ai.planner import Planner

from app.character.character import Character

from tests.character_database import CharacterDatabase


def main():

    database = CharacterDatabase()

    character = database.load_character()

    if character is None:

        character = Character(
            name="Мира",
            age=20
        )

        character.personality.backstory = (
            "Мира — живой виртуальный персонаж, "
            "который постепенно развивается "
            "через общение с пользователем."
        )

        character.personality.behavior_style = (
            "Дружелюбная, любопытная, "
            "иногда саркастичная."
        )

        character.personality.add_trait(
            "Любопытная"
        )

        character.personality.add_trait(
            "Самостоятельная"
        )

        character.personality.add_like(
            "интересные разговоры"
        )

        character.personality.add_like(
            "программирование"
        )

        character.personality.add_rule(
            "Не отвечать шаблонно."
        )

        database.save_character(
            character
        )

    llm = LocalLLM()

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

    print()
    print("=" * 60)
    print("DESKTOP PET — QWEN3 LOCAL")
    print("=" * 60)
    print()

    print(
        f"Персонаж: {character.name}"
    )

    print(
        "Модель: Qwen3-8B-Q4_K_M"
    )

    print(
        "Сервер: http://127.0.0.1:8080"
    )

    print()

    while True:

        message = input(
            "Ты: "
        ).strip()

        if not message:

            continue

        if message.lower() == "exit":

            break

        if message.lower() == "personality":

            print()
            print(
                character
                .get_personality_description()
            )
            print()

            continue

        if message.lower() == "stats":

            print()
            print(
                database.statistics()
            )
            print()

            continue

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
            print(
                "Ошибка:"
            )

            print(error)

            print()


if __name__ == "__main__":
    main()