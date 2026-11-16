from typing import Callable

from .stt import SpeechToText


class VoiceManager:

    def __init__(
        self,
        on_text: Callable[[str], None]
    ):
        self.on_text = on_text

        self.stt = SpeechToText()

        self.running = False

    def start(self):

        if self.running:
            return

        self.running = True

        self.stt.start(
            self._on_speech
        )

    def _on_speech(
        self,
        text: str
    ):

        if not text:
            return

        text = text.strip()

        if not text:
            return

        print(
            f"🎤 Пользователь: {text}"
        )

        self.on_text(
            text
        )

    def stop(self):

        if not self.running:
            return

        self.running = False

        self.stt.stop()