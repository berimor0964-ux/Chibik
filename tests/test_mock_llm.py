import unittest

from app.ai.context import AIContext
from app.ai.llm import MockLLM
from app.character.character import Character


class MockLLMTests(unittest.TestCase):
    def setUp(self):
        self.character = Character(name="Мира", age=1)
        self.llm = MockLLM()

    def test_greeting_is_not_a_plain_echo(self):
        answer = self.llm.generate(AIContext(character=self.character, user_message="Привет!"))
        self.assertIn("Привет", answer)
        self.assertIn("Мира", answer)
        self.assertNotIn("Я получил твоё сообщение", answer)

    def test_status_uses_character_needs(self):
        self.character.needs.energy = 10
        answer = self.llm.generate(AIContext(character=self.character, user_message="Как ты?"))
        self.assertIn("сонная", answer)

    def test_fallback_is_transparent_about_offline_mode(self):
        answer = self.llm.generate(AIContext(character=self.character, user_message="Расскажи про космос"))
        self.assertIn("автономном режиме", answer)


if __name__ == "__main__":
    unittest.main()
