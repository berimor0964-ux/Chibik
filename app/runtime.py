"""Runtime связывает персонажа, мир, AI-поведение и интерфейс Chibik.

Внешняя LLM подключается только при наличии LOCAL_LLM_URL и пакета openai.
Без неё персонаж использует локальный безопасный диалог и автономную логику.
"""
from __future__ import annotations

import os
import random
import json
import threading
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot, QTimer

from app.character.character import Character
from app.character.memory import MemoryType
from app.character.behavior import Behavior
from app.character.actions import ActionType
from app.world.world import World
from app.world.zone import Zone
from app.world.objects import WorldObject
from app.world.navigation import Navigation


class ChibikRuntime(QObject):
    replyReady = Signal(str)
    userMessageReceived = Signal(str)
    characterMoved = Signal(float, float)
    characterStateChanged = Signal(str)
    needsChanged = Signal(str)
    voiceStatusChanged = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.world = World("Дом Миры")
        self.zone = Zone("Комната", width=18, height=10)
        self.world.add_zone(self.zone)

        self.character = Character(name="Мира", age=19)
        self.character.personality.traits = ["любопытная", "добрая", "немного упрямая"]
        self.character.personality.behavior_style = "дружелюбная, живая, любознательная"
        self.character.personality.backstory = "Живёт в своей уютной комнате и любит исследовать её."
        self.character.state.x = 1.0
        self.character.state.y = 4.0

        self.avatar = WorldObject(
            x=1.0, y=4.0, width=0.65, height=0.75,
            solid=True, name="Мира", id=self.character.id
        )
        self.zone.add_object(self.avatar)

        self.objects = {}
        self._add_object("Кровать", 2, 1, 3, 2, "bed")
        self._add_object("Стол", 7, 1, 2, 1.2, "desk")
        self._add_object("Шкаф", 12, 1, 1.4, 1.4, "wardrobe")
        self._add_object("Растение", 2, 7, 1, 1, "plant")
        self._add_object("Диван", 8, 6.5, 2, 1, "sofa")
        self._add_object("Тумба", 14, 6, 1.3, 1.3, "cabinet")

        self._active_path = []
        self._pending_action = None
        self._autonomy_enabled = True
        self._tick_count = 0
        self._state_ticks = 0
        self._voice = None
        self._voice_text.connect(self._on_voice_text)
        self._tts = None
        self._llm = None
        self._try_load_llm()
        self._state_file = Path(__file__).resolve().parents[1] / "data" / "mira_state.json"
        self._load_state()

        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._tick)
        self.timer.start()

    def _add_object(self, name, x, y, width, height, kind):
        obj = WorldObject(x=x, y=y, width=width, height=height,
                          solid=True, name=name)
        self.zone.add_object(obj)
        self.objects[kind] = obj

    def _try_load_llm(self):
        try:
            from dotenv import load_dotenv
            load_dotenv(Path(__file__).resolve().parents[1] / ".env")
        except ImportError:
            pass
        if not os.getenv("LOCAL_LLM_URL"):
            return
        try:
            from app.ai.llm import LocalLLM
            self._llm = LocalLLM()
        except Exception as exc:
            print(f"[Chibik] Локальная LLM не подключена: {exc}")

    def _move_to(self, x: float, y: float) -> bool:
        try:
            path = Navigation.find_path(self.avatar, self.zone, x, y, step=1.0)
        except (ValueError, TypeError):
            return False
        if not path:
            return False
        self._active_path = path[1:]
        if self._active_path:
            self.character.state.current_action = "walk"
            self.characterStateChanged.emit("walk")
        return True

    def _step_movement(self):
        if not self._active_path:
            return
        x, y = self._active_path.pop(0)
        self.avatar.x, self.avatar.y = x, y
        self.character.state.x, self.character.state.y = x, y
        self.characterMoved.emit(x, y)
        if not self._active_path:
            if self._pending_action:
                pending = self._pending_action
                self._pending_action = None
                self._complete_action(pending)
            else:
                self.character.state.current_action = "idle"
                self.characterStateChanged.emit("idle")

    def _tick(self):
        self._tick_count += 1
        self._step_movement()
        if self._state_ticks > 0:
            self._state_ticks -= 1
            if self._state_ticks == 0 and not self._active_path:
                self.character.state.current_action = "idle"
                self.characterStateChanged.emit("idle")

        # Потребности постепенно меняются во времени, но не быстрее реального времени.
        if self._tick_count % 5 == 0:
            n = self.character.needs
            n.change_hunger(-0.7)
            n.change_energy(-0.45)
            n.change_fun(-0.25)
            n.change_social(-0.2)
            n.change_hygiene(-0.15)
            n.change_comfort(-0.1)

        if self._autonomy_enabled and not self._active_path and self._tick_count % 8 == 0:
            self._autonomous_decision()
        if self._tick_count % 5 == 0:
            self._update_mood()
            self.needsChanged.emit(self.needsSummary())
        if self._tick_count % 30 == 0:
            self._save_state()

    def _autonomous_decision(self):
        goal = Behavior(self.character).evaluate()
        if goal is None:
            # В отсутствие срочной потребности Мира иногда исследует комнату.
            if random.random() < 0.25:
                self._wander()
            return

        actions = {
            "sleep": ("bed", 15, 3, "sleep", "Пойду немного посплю."),
            "eat": ("desk", 8, 3, "eat", "Кажется, я проголодалась."),
            "wash": ("cabinet", 14, 5, "wash", "Нужно привести себя в порядок."),
            "socialize": (None, None, None, "idle", "Хочется немного пообщаться!"),
            "have_fun": ("plant", 3, 7, "play", "Поищу, чем себя развлечь."),
            "relax": ("sofa", 9, 7, "relax", "Пожалуй, немного отдохну."),
        }
        item = actions.get(goal.type.value)
        if not item:
            return
        target_kind, tx, ty, state, _ = item
        if target_kind:
            # Позиции рядом с предметами, а не внутри их коллизии.
            target = {
                "bed": (5, 3), "desk": (6, 3), "cabinet": (13, 5),
                "plant": (4, 7), "sofa": (7, 7)
            }[target_kind]
            if self._move_to(*target):
                self._pending_action = state
                self.characterStateChanged.emit("walk")
                return
        self._complete_action(state)

    def _wander(self):
        candidates = [(5, 5), (10, 4), (16, 5), (5, 8), (16, 8)]
        random.shuffle(candidates)
        for point in candidates:
            if self._move_to(*point):
                return

    def _complete_action(self, action: str):
        n = self.character.needs
        if action == "sleep":
            n.change_energy(25)
        elif action == "eat":
            n.change_hunger(25)
        elif action == "play":
            n.change_fun(20)
        elif action == "relax":
            n.change_energy(8)
            n.change_comfort(18)
        elif action == "wash":
            n.change_hygiene(30)
        self.character.state.current_action = action
        self._state_ticks = 6 if action == "sleep" else 3
        self.characterStateChanged.emit(action)

    @Slot(result=str)
    def needsSummary(self) -> str:
        n = self.character.needs
        return (f"Энергия {n.energy:.0f}% · Голод {n.hunger:.0f}% · "
                f"Веселье {n.fun:.0f}% · Общение {n.social:.0f}% · "
                f"Гигиена {n.hygiene:.0f}% · Комфорт {n.comfort:.0f}%")

    def _update_mood(self):
        n = self.character.needs
        if n.energy < 20:
            mood = "сонное"
        elif n.hunger < 20:
            mood = "раздражённое"
        elif n.fun < 20:
            mood = "скучающее"
        elif n.social < 20:
            mood = "одинокое"
        elif n.fun > 75 and n.energy > 60:
            mood = "радостное"
        else:
            mood = "спокойное"
        self.character.state.mood = mood

    def _load_state(self):
        if not self._state_file.exists():
            return
        try:
            data = json.loads(self._state_file.read_text(encoding="utf-8"))
            for key, value in data.get("needs", {}).items():
                if hasattr(self.character.needs, key):
                    setattr(self.character.needs, key, max(0.0, min(100.0, float(value))))
            for key, value in data.get("personality", {}).items():
                if hasattr(self.character.personality, key) and isinstance(value, (int, float, str, list)):
                    setattr(self.character.personality, key, value)
            self.character.state.x = float(data.get("position", {}).get("x", self.avatar.x))
            self.character.state.y = float(data.get("position", {}).get("y", self.avatar.y))
            self.avatar.x = self.character.state.x
            self.avatar.y = self.character.state.y
            self.character.state.mood = str(data.get("mood", "спокойное"))
            for entry in data.get("memories", [])[-200:]:
                self.character.memory.remember(
                    content=str(entry.get("content", "")),
                    memory_type=MemoryType(entry.get("type", "short_term")),
                    importance=float(entry.get("importance", 30)),
                    metadata=entry.get("metadata", {}),
                )
        except Exception as exc:
            print(f"[Chibik] Не удалось загрузить состояние: {exc}")

    def _save_state(self):
        try:
            self._state_file.parent.mkdir(parents=True, exist_ok=True)
            needs = vars(self.character.needs)
            personality = {
                key: value for key, value in vars(self.character.personality).items()
                if isinstance(value, (int, float, str, list))
            }
            memories = [{
                "content": item.content,
                "type": item.memory_type.value,
                "importance": item.importance,
                "metadata": item.metadata,
            } for item in self.character.memory.memories[-200:]]
            payload = {
                "saved_at": datetime.now().isoformat(timespec="seconds"),
                "position": {"x": self.avatar.x, "y": self.avatar.y},
                "mood": self.character.state.mood,
                "needs": needs,
                "personality": personality,
                "memories": memories,
            }
            temp = self._state_file.with_suffix(".tmp")
            temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            temp.replace(self._state_file)
        except Exception as exc:
            print(f"[Chibik] Не удалось сохранить состояние: {exc}")

    def _world_tool_schemas(self):
        return [
            {"type": "function", "function": {
                "name": "move_character",
                "description": "Переместить Миру в свободную точку её комнаты.",
                "parameters": {"type": "object", "properties": {
                    "x": {"type": "number", "description": "Координата X от 0 до 17"},
                    "y": {"type": "number", "description": "Координата Y от 0 до 9"}},
                    "required": ["x", "y"]}}},
            {"type": "function", "function": {
                "name": "inspect_world",
                "description": "Получить положение Миры, предметы и потребности.",
                "parameters": {"type": "object", "properties": {}, "required": []}}},
            {"type": "function", "function": {
                "name": "interact_with_object",
                "description": "Взаимодействовать с предметом комнаты: bed, desk, wardrobe, plant, sofa, cabinet.",
                "parameters": {"type": "object", "properties": {
                    "object": {"type": "string", "enum": ["bed", "desk", "wardrobe", "plant", "sofa", "cabinet"]}},
                    "required": ["object"]}}},
        ]

    def _execute_world_tool(self, name, args):
        if name == "move_character":
            x, y = float(args["x"]), float(args["y"])
            if not (0 <= x <= 17 and 0 <= y <= 9):
                return {"ok": False, "reason": "Точка за пределами комнаты."}
            moved = self._move_to(x, y)
            return {"ok": moved, "message": "Маршрут построен." if moved else "Путь заблокирован."}
        if name == "inspect_world":
            return {"position": [self.avatar.x, self.avatar.y],
                    "objects": {k: v.name for k, v in self.objects.items()},
                    "needs": self.needsSummary(), "mood": self.character.state.mood}
        if name == "interact_with_object":
            key = args["object"]
            targets = {"bed": (5, 3, "sleep"), "desk": (6, 3, "eat"),
                       "wardrobe": (13, 5, "wash"), "plant": (4, 7, "play"),
                       "sofa": (7, 7, "relax"), "cabinet": (13, 5, "wash")}
            if key not in targets:
                return {"ok": False, "reason": "Неизвестный предмет."}
            x, y, action = targets[key]
            moved = self._move_to(x, y)
            if moved:
                self._pending_action = action
            return {"ok": moved, "message": f"Мира направляется к {self.objects[key].name}." if moved else "Не удалось построить маршрут."}
        return {"ok": False, "reason": "Инструмент не найден."}

    def _local_reply(self, message: str) -> str:
        text = message.lower().strip()
        n = self.character.needs
        rel = self.character.relationships.get_or_create("user")
        if any(w in text for w in ("привет", "здравствуй", "доброе утро")):
            rel.change_friendship(1)
            return random.choice(["Привет! Рада тебя видеть 💛", "О, ты вернулся! Как дела?", "Привет-привет! Я тут осматривала комнату."])
        if any(w in text for w in ("как дела", "как ты", "как настроение")):
            return f"У меня {self.character.state.mood} настроение. {self.needsSummary()}"
        if"кто ты" in text or "как тебя зовут" in text:
            return "Я Мира! Это моя комната, и мне здесь нравится. Я могу гулять, отдыхать и болтать с тобой."
        if any(w in text for w in ("иди", "подойди", "пройди", "перейди")):
            points = [(5, 5), (10, 4), (16, 5), (5, 8), (16, 8)]
            target = random.choice(points)
            return "Хорошо, сейчас подойду!" if self._move_to(*target) else "Не получается пройти туда — путь занят."
        if any(w in text for w in ("спи", "поспи", "отдохни")):
            if self._move_to(5, 3):
                n.change_energy(8)
                return "Иду к кровати. Немного посплю."
            return "К кровати сейчас не пройти."
        if any(w in text for w in ("поиграй", "развлекись", "поиграть")):
            n.change_fun(8)
            self._wander()
            return "Поищу что-нибудь интересное!"
        if any(w in text for w in ("помнишь", "что ты помнишь")):
            memories = self.character.memory.get_recent(5)
            return "Я помню:\n" + "\n".join("• " + x.content for x in memories) if memories else "Пока у меня ещё мало воспоминаний. Давай создадим их вместе!"
        if any(w in text for w in ("состояние", "потребности", "статус")):
            return self.needsSummary()
        if any(w in text for w in ("спасибо", "молодец", "умница")):
            rel.change_affection(1)
            return "Хи-хи, спасибо! Мне приятно 😊"
        if"?" in message or any(w in text for w in ("почему", "зачем", "расскажи")):
            return "Хороший вопрос! Я пока изучаю этот мир. Расскажешь, что ты сам об этом думаешь?"
        return random.choice([
            "Я тебя слушаю. Расскажи ещё!",
            "Хм, интересно. Я запомню наш разговор.",
            "Мне нравится с тобой болтать. А я пока осмотрю комнату.",
        ])

    @Slot(str, result=str)
    def sendMessage(self, message: str) -> str:
        message = (message or "").strip()
        if not message:
            return ""
        self.userMessageReceived.emit(message)
        self.character.memory.remember(
            message, MemoryType.SHORT_TERM, importance=35,
            metadata={"type": "user_message"})
        self.character.personality.develop_from_message(message)
        try:
            if self._llm:
                from app.ai.context import AIContext
                context = AIContext(
                    character=self.character,
                    user_message=message,
                    memories=self.character.memory.get_recent(15),
                    world_data={
                        "room": self.zone.name,
                        "objects": [o.name for o in self.zone.objects.values()],
                        "position": [self.avatar.x, self.avatar.y],
                    },
                )
                response = self._llm.generate_with_tools(
                    context=context,
                    tools=self._world_tool_schemas(),
                    tool_executor=self._execute_world_tool,
                    max_tool_rounds=3,
                )
            else:
                response = self._local_reply(message)
        except Exception as exc:
            print(f"[Chibik] Ошибка LLM, включён локальный ответ: {exc}")
            response = self._local_reply(message)

        self.character.memory.remember_interaction(message, response)
        self.character.needs.change_social(3)
        self._save_state()
        self.replyReady.emit(response)
        return response

    @Slot(str)
    def characterAction(self, action: str):
        commands = {
            "feed": ("eat", (6, 3)),
            "sleep": ("sleep", (5, 3)),
            "play": ("play", (4, 7)),
            "talk": ("talk", None),
            "state": ("state", None),
        }
        item = commands.get(action)
        if not item:
            return
        kind, point = item
        if point:
            self._move_to(*point)
        if kind == "eat":
            self.character.needs.change_hunger(15)
        elif kind == "sleep":
            self.character.needs.change_energy(15)
        elif kind == "play":
            self.character.needs.change_fun(15)
        self.character.state.current_action = kind
        self.characterStateChanged.emit(kind)

    @Slot(bool)
    def setAutonomy(self, enabled: bool):
        self._autonomy_enabled = bool(enabled)

    @Slot(result=str)
    def startVoice(self) -> str:
        if self._voice:
            return "Голосовой ввод уже запущен."
        try:
            from app.voice.stt import SpeechToText
            self._voice = SpeechToText(device="cpu", compute_type="int8")
            self._voice.start(lambda text: self._voice_message(text))
            self.voiceStatusChanged.emit("Микрофон активен")
            return "Микрофон активен"
        except Exception as exc:
            self._voice = None
            message = f"Не удалось запустить микрофон: {exc}"
            self.voiceStatusChanged.emit(message)
            return message

    def _voice_message(self, text: str):
        # Callback STT вызывается из рабочего потока; сигнал безопасно доставит его в Qt.
        self._voice_text.emit(text)

    _voice_text = Signal(str)

    def _on_voice_text(self, text):
        self.sendMessage(text)

    @Slot(result=str)
    def stopVoice(self) -> str:
        if self._voice:
            self._voice.stop()
            self._voice = None
        self.voiceStatusChanged.emit("Голосовой ввод выключен")
        return "Голосовой ввод выключен"

    @Slot(str)
    def speak(self, text: str):
        threading.Thread(
            target=self._speak_worker,
            args=(str(text),),
            daemon=True,
        ).start()

    def _speak_worker(self, text: str):
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.say(text)
            engine.runAndWait()
            engine.stop()
        except Exception as exc:
            self.voiceStatusChanged.emit(f"Озвучивание недоступно: {exc}")

    def close(self):
        self.timer.stop()
        self.stopVoice()
        self._save_state()
