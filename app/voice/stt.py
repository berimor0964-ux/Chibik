import queue
import threading
import time

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel


class SpeechToText:

    def __init__(
        self,
        model_size: str = "small",
        device: str = "cuda",
        compute_type: str = "float16",
        sample_rate: int = 16000,
        silence_threshold: float = 0.01,
        silence_duration: float = 1.2,
        max_recording_duration: float = 15.0,
    ):
        self.sample_rate = sample_rate

        self.silence_threshold = (
            silence_threshold
        )

        self.silence_duration = (
            silence_duration
        )

        self.max_recording_duration = (
            max_recording_duration
        )

        self.audio_queue = queue.Queue()

        self.running = False

        self.thread = None

        print(
            "Загрузка модели распознавания речи..."
        )

        self.model = WhisperModel(
            model_size,
            device=device,
            compute_type=compute_type
        )

        print(
            "Модель распознавания речи загружена."
        )

    def _audio_callback(
        self,
        indata,
        frames,
        time_info,
        status
    ):
        if status:
            print(
                f"Microphone: {status}"
            )

        audio = indata[:, 0].copy()

        self.audio_queue.put(
            audio
        )

    def _get_audio_level(
        self,
        audio: np.ndarray
    ) -> float:

        if len(audio) == 0:
            return 0.0

        return float(
            np.sqrt(
                np.mean(
                    np.square(audio)
                )
            )
        )

    def _record_phrase(self):

        chunks = []

        speaking = False

        silence_time = 0.0

        recording_time = 0.0

        block_duration = 0.1

        while self.running:

            try:

                audio = (
                    self.audio_queue.get(
                        timeout=1.0
                    )
                )

            except queue.Empty:

                continue

            chunks.append(audio)

            recording_time += (
                block_duration
            )

            level = (
                self._get_audio_level(
                    audio
                )
            )

            if level >= self.silence_threshold:

                speaking = True

                silence_time = 0.0

            elif speaking:

                silence_time += (
                    block_duration
                )

            if (
                speaking
                and silence_time
                >= self.silence_duration
            ):

                break

            if (
                recording_time
                >= self.max_recording_duration
            ):

                break

        if not chunks:

            return None

        return np.concatenate(
            chunks
        )

    def transcribe(
        self,
        audio: np.ndarray
    ) -> str:

        segments, info = (
            self.model.transcribe(
                audio,
                language="ru",
                beam_size=5,
                vad_filter=True,
                condition_on_previous_text=False
            )
        )

        text = " ".join(
            segment.text.strip()
            for segment in segments
        )

        return text.strip()

    def listen_once(self) -> str | None:

        audio = self._record_phrase()

        if audio is None:
            return None

        if len(audio) == 0:
            return None

        text = self.transcribe(
            audio
        )

        if not text:
            return None

        return text

    def start(
        self,
        callback
    ):

        if self.running:
            return

        self.running = True

        self.thread = threading.Thread(
            target=self._listen_loop,
            args=(callback,),
            daemon=True
        )

        self.thread.start()

    def _listen_loop(
        self,
        callback
    ):

        with sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="float32",
            blocksize=1600,
            callback=self._audio_callback
        ):

            print(
                "🎤 Голосовой ввод активен."
            )

            while self.running:

                try:

                    text = (
                        self.listen_once()
                    )

                    if text:

                        callback(text)

                except Exception as error:

                    print(
                        "Ошибка STT:"
                    )

                    print(error)

                    time.sleep(1)

    def stop(self):

        self.running = False

        if self.thread:

            self.thread.join(
                timeout=2
            )

            self.thread = None

        print(
            "🎤 Голосовой ввод остановлен."
        )