from app.ai.agent import Agent
from app.ai.llm import LocalLLM
from app.ai.planner import Planner

from app.character.character import Character

from app.voice.voice_manager import VoiceManager

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
            "Мира — живой виртуальный персонаж."
        )

        character.personality.behavior_style = (
            "Дружелюбная, любопытная и живая."
        )

        character.personality.add_trait(
            "Любопытная"
        )

        character.personality.add_trait(
            "Дружелюбная"
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

    def process_voice_message(
        text: str
    ):

        print()

        print(
            f"🧠 Qwen получает: {text}"
        )

        try:

            response = agent.chat(
                text
            )

            print()

            print(
                f"🤖 {character.name}:"
            )

            print(response)

            print()

        except Exception as error:

            print(
                "Ошибка AI:"
            )

            print(error)

    voice = VoiceManager(
        on_text=process_voice_message
    )

    voice.start()

    print()
    print("=" * 60)
    print("DESKTOP PET — VOICE AI")
    print("=" * 60)
    print()
    print(
        "🎤 Говори в микрофон."
    )
    print(
        "Нажми Ctrl+C для остановки."
    )
    print()

    try:

        while True:

            import time

            time.sleep(1)

    except KeyboardInterrupt:

        print()
        print(
            "Остановка..."
        )

        voice.stop()


if __name__ == "__main__":
    main()