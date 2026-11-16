"""Связка экранного питомца с моделью World/Zone/Physics/Navigation."""
from __future__ import annotations

import math
import random

from PySide6.QtCore import QObject, QTimer, Signal, QRect
from PySide6.QtGui import QGuiApplication

from app.ai.agent import Agent
from app.ai.llm import LocalLLM, MockLLM
from app.ai.planner import Planner
from app.character.character import Character
from app.character.actions import ActionType
from app.world.navigation import Navigation
from app.world.objects import WorldObject
from app.world.physics import Physics
from app.world.world import World
from app.world.zone import Zone

CELL_SIZE = 32
SPRITE_SIZE = 128


class DesktopWalkTool:
    name = "desktop_walk"
    description = (
        "Переместить Миру в другую точку рабочего стола. Координаты x и y "
        "измеряются клетками по 32 пикселя от левого верхнего угла."
    )

    def __init__(self, controller):
        self.controller = controller

    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "x": {"type": "integer", "description": "Целевая клетка по горизонтали"},
                "y": {"type": "integer", "description": "Целевая клетка по вертикали"},
            },
            "required": ["x", "y"],
            "additionalProperties": False,
        }

    def to_openai_tool(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters_schema(),
            },
        }

    def execute(self, x: int, y: int) -> dict:
        max_x = max(0, self.controller.grid_width - int(self.controller.pet.width))
        max_y = max(0, self.controller.grid_height - int(self.controller.pet.height))
        x, y = int(x), int(y)
        if not (0 <= x <= max_x and 0 <= y <= max_y):
            return {"status": "rejected", "reason": "Координаты за границами",
                    "max_x": max_x, "max_y": max_y}
        self.controller.walkRequested.emit(x, y)
        return {"status": "movement_requested", "x": x, "y": y}


class DesktopWorldController(QObject):
    positionChanged = Signal(int, int)
    stateChanged = Signal(str, str)
    speechRequested = Signal(str)
    needsChanged = Signal(float, float, float)
    walkRequested = Signal(int, int)
    sceneChanged = Signal(str)

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)

        screen = QGuiApplication.primaryScreen()
        if screen is None:
            raise RuntimeError("Не удалось определить экран для Desktop Pet.")

        screen_geometry = screen.availableGeometry()
        house_width = min(640, max(480, screen_geometry.width() - 32))
        house_height = min(420, max(360, screen_geometry.height() - 32))
        house_x = screen_geometry.x() + screen_geometry.width() - house_width
        house_y = screen_geometry.y() + screen_geometry.height() - house_height

        self.geometry = QRect(house_x, house_y, house_width, house_height)
        self.grid_width = max(8, self.geometry.width() // CELL_SIZE)
        self.grid_height = max(8, self.geometry.height() // CELL_SIZE)

        # Ограничение блуждания только полом (нижние 38% высоты)
        self.floor_y_min = max(0, int(self.grid_height * 0.62))

        self.world = World("Рабочий стол")
        self.zone = Zone("Рабочий стол",
                         width=float(self.grid_width),
                         height=float(self.grid_height))
        self.world.add_zone(self.zone)

        self.pet = WorldObject(
            x=float(max(0, self.grid_width // 2 - 2)),
            y=float(self.grid_height - 4),
            width=4.0, height=4.0, solid=True, name="Мира",
        )
        self.world.add_object(self.zone.name, self.pet)

        self.character = Character(name="Мира", age=1)

        # Агент (ОБЯЗАТЕЛЬНО до использования self.agent.tools)
        self.agent = self._create_agent(self.character)

        self.walkRequested.connect(self.request_walk_to)
        self.agent.tools["desktop_walk"] = DesktopWalkTool(self)

        self._path: list[tuple[float, float]] = []
        self._path_index = 0
        self._paused = False
        self._state = "idle"
        self._direction = "right"
        self.auto_rotate = True

        self._elapsed = 0.0
        self._needs_elapsed = 0.0
        self._behavior_elapsed = 0.0
        self._wander_elapsed = 0.0
        self._sleeping = False
        self._temporary_state_time = 0.0

        # Логика комнат
        self._scene_mode = "room"
        self._transition_after_path = None
        self._random = random.Random()

        # Таймер
        self.timer = QTimer(self)
        self.timer.setInterval(16)
        self.timer.timeout.connect(self.tick)
        self.timer.start()

        # База данных (в try/except, чтобы не блокировать запуск)
        self.db = None
        try:
            from app.database.database import Database
            self.db = Database()
            self.db.create_character("mira", self.character.name, self.character.age)
            self.db.set_active_character("mira")
            self._load_from_db()
            # Автосохранение каждые 60 секунд
            self._autosave_timer = QTimer(self)
            self._autosave_timer.setInterval(60_000)
            self._autosave_timer.timeout.connect(self._save_to_db)
            self._autosave_timer.start()
        except Exception as e:
            print(f"Предупреждение: БД недоступна, работаем без сохранения: {e}")

        QTimer.singleShot(0, self._emit_position)
        self._emit_state()
        self._emit_needs()

    @staticmethod
    def _create_agent(character: Character) -> Agent:
        import os
        mode = os.getenv("CHIBIK_LLM", "mock").strip().lower()
        llm = MockLLM()
        if mode == "local":
            try:
                llm = LocalLLM()
            except Exception as error:
                print(f"Предупреждение: локальная LLM недоступна. Причина: {error}",
                      flush=True)
        return Agent(character=character, llm=llm, planner=Planner())

    @property
    def state(self) -> str:
        return self._state

    @property
    def direction(self) -> str:
        return self._direction

    @property
    def scene_mode(self) -> str:
        return self._scene_mode

    def _emit_position(self) -> None:
        x = self.geometry.x() + round(self.pet.x * CELL_SIZE)
        y = self.geometry.y() + round(self.pet.y * CELL_SIZE)
        self.positionChanged.emit(x, y)

    def _emit_state(self) -> None:
        self.stateChanged.emit(self._state, self._direction)

    def _emit_needs(self) -> None:
        needs = self.character.needs
        self.needsChanged.emit(float(needs.energy),
                               float(needs.hunger),
                               float(needs.fun))

    def pause(self) -> None:
        self._paused = True

    def resume(self) -> None:
        self._paused = False

    def set_auto_rotate(self, enabled: bool) -> None:
        self.auto_rotate = bool(enabled)
        self._emit_state()

    def set_window_position(self, x: int, y: int) -> None:
        gx = (x - self.geometry.x()) / CELL_SIZE
        gy = (y - self.geometry.y()) / CELL_SIZE
        gx = min(max(0.0, gx), self.zone.width - self.pet.width)
        gy = min(max(0.0, gy), self.zone.height - self.pet.height)
        self.pet.x, self.pet.y = gx, gy
        self._path.clear()
        self._path_index = 0
        self._transition_after_path = None
        self._set_state("idle")
        self._emit_position()

    def _set_state(self, state: str) -> None:
        if self._state != state:
            self._state = state
            self.character.state.current_action = state
            self._emit_state()

    def _start_walk(self, target_x: int | None = None,
                    target_y: int | None = None) -> bool:
        max_x = max(0, self.grid_width - int(self.pet.width))
        max_y = max(0, self.grid_height - int(self.pet.height))

        if target_x is None:
            target_x = self._random.randint(0, max_x)
        if target_y is None:
            # В комнате Мира ходит только по полу
            if self._scene_mode == "room":
                target_y = self._random.randint(self.floor_y_min, max_y)
            else:
                target_y = self._random.randint(0, max_y)

        start = (round(self.pet.x), round(self.pet.y))
        target = (float(min(max_x, max(0, target_x))),
                  float(min(max_y, max(0, target_y))))

        if abs(self.pet.x - start[0]) > 1e-6 or abs(self.pet.y - start[1]) > 1e-6:
            self.pet.x, self.pet.y = float(start[0]), float(start[1])
            self._emit_position()

        path = Navigation.find_path(self.pet, self.zone,
                                    target[0], target[1], step=1.0)
        if not path:
            return False

        self._path = path
        self._path_index = 1
        if len(path) <= 1:
            self._set_state("idle")
            return False

        self._set_state("walk")
        return True

    # ========== ЛОГИКА ДВЕРИ ==========

    def request_walk(self) -> None:
        """Мира доходит до левой двери и выходит во двор."""
        self._sleeping = False
        if self._scene_mode == "room":
            door_x = 1.0  # Дверь слева
            door_y = max(0, self.grid_height - int(self.pet.height))
            self._transition_after_path = "outside"
            if not self._start_walk(door_x, door_y):
                self._enter_outside()
        else:
            self._start_walk()

    def request_home(self) -> None:
        """Мира возвращается к левой двери и входит в комнату."""
        self._sleeping = False
        if self._scene_mode == "room":
            self.speechRequested.emit("Я уже дома! ♥")
            return
        door_x = 1.0  # Дверь слева
        door_y = max(0, self.grid_height - int(self.pet.height))
        self._transition_after_path = "room"
        if not self._start_walk(door_x, door_y):
            self._enter_room()

    def _enter_outside(self) -> None:
        """Мира вышла через левую дверь."""
        self._transition_after_path = None
        self._scene_mode = "outside"
        self.pet.x = 2.0  # Чуть правее двери
        self.pet.y = float(max(0, self.grid_height - int(self.pet.height)))
        self.sceneChanged.emit(self._scene_mode)
        self._emit_position()
        self._set_state("idle")
        self._wander_elapsed = 0.0
        self._start_walk()

    def _enter_room(self) -> None:
        """Мира вошла через левую дверь в комнату."""
        self._transition_after_path = None
        self._scene_mode = "room"
        self.pet.x = 1.0  # У левой двери
        self.pet.y = float(max(0, self.grid_height - int(self.pet.height)))
        self.sceneChanged.emit(self._scene_mode)
        self._emit_position()
        self._set_state("idle")
        self._wander_elapsed = 0.0
        # Через полсекунды идёт в центр комнаты
        QTimer.singleShot(500, lambda: self._start_walk(
            max(0, self.grid_width // 2 - 2),
            self._random.randint(self.floor_y_min,
                                 max(0, self.grid_height - int(self.pet.height)))
        ))

    def request_walk_to(self, x: int, y: int) -> None:
        self._sleeping = False
        self._transition_after_path = None
        if not self._start_walk(int(x), int(y)):
            self.speechRequested.emit("Я не смогла найти безопасный путь туда.")

    def perform_action(self, action: str) -> str:
        action = (action or "").lower()
        needs = self.character.needs

        if action in ("walk", "explore"):
            self.request_walk()
            self.speechRequested.emit("Пойду немного прогуляюсь!")
        elif action == "home":
            self.request_home()
            self.speechRequested.emit("Возвращаюсь домой!")
        elif action == "sleep":
            self._path.clear()
            self._transition_after_path = None
            self._sleeping = True
            self._set_state("sleep")
            self.speechRequested.emit("Пора поспать…")
        elif action == "feed":
            needs.change_hunger(35)
            self._sleeping = False
            if self._state == "sleep":
                self._set_state("idle")
            self.speechRequested.emit("Спасибо за угощение! ♥")
            self._emit_needs()
        elif action == "state":
            self.speechRequested.emit(
                f"Энергия: {needs.energy:.0f}%, "
                f"голод: {needs.hunger:.0f}%, "
                f"веселье: {needs.fun:.0f}%")
        elif action == "memory":
            memories = self.character.memory.get_recent(limit=1)
            self.speechRequested.emit(
                memories[-1].content if memories
                else "Мы пока только знакомимся!")
        elif action == "talk":
            self.speechRequested.emit("Я здесь! Напиши мне в чате.")
        elif action == "settings":
            return "settings"
        elif action == "quit":
            return "quit"

        self._emit_needs()
        return action

    def answer_chat(self, message: str) -> str:
        reply = self.agent.chat(message)
        if self.db:
            try:
                self.db.save_interaction(message, reply, "mira")
            except Exception:
                pass
        return reply

    def tick(self) -> None:
        dt = min(self.timer.interval() / 1000.0, 0.05)
        if self._paused:
            return

        self._elapsed += dt
        self._needs_elapsed += dt
        self._behavior_elapsed += dt
        self._wander_elapsed += dt

        if self._needs_elapsed >= 5.0:
            elapsed = self._needs_elapsed
            self._needs_elapsed = 0.0
            needs = self.character.needs
            needs.change_hunger(-0.18 * elapsed)
            needs.change_fun(-0.12 * elapsed)
            needs.change_social(-0.035 * elapsed)
            needs.change_hygiene(-0.025 * elapsed)
            needs.change_comfort(-0.02 * elapsed)
            if not self._sleeping:
                needs.change_energy(-0.10 * elapsed)
            else:
                needs.change_energy(2.5 * elapsed)
                if needs.energy >= 80:
                    self._sleeping = False
                    self._set_state("idle")
                    self.speechRequested.emit("Я выспалась!")
            self._emit_needs()

        if self._behavior_elapsed >= 1.0:
            self._behavior_elapsed = 0.0
            if self._transition_after_path is None:
                action = self.agent.update()
                if action:
                    self._apply_behavior_action(action.type)

        if self._temporary_state_time > 0:
            self._temporary_state_time = max(0.0,
                                             self._temporary_state_time - dt)
            if self._temporary_state_time == 0 and self._state == "stand":
                self._set_state("idle")

        if self._state == "walk" and self._path_index < len(self._path):
            target_x, target_y = self._path[self._path_index]
            dx, dy = target_x - self.pet.x, target_y - self.pet.y
            distance = math.hypot(dx, dy)
            step = 2.8 * dt

            if distance <= step or distance < 1e-5:
                nx, ny = target_x, target_y
                self._path_index += 1
            else:
                nx = self.pet.x + dx / distance * step
                ny = self.pet.y + dy / distance * step

            if Physics.can_move(self.pet, self.zone, nx, ny):
                self.pet.x, self.pet.y = nx, ny
                if self.auto_rotate:
                    if dx < -1e-4:
                        self._direction = "left"
                    elif dx > 1e-4:
                        self._direction = "right"
                self._emit_position()
                self._emit_state()
            else:
                self._path.clear()
                self._set_state("idle")

            if self._path_index >= len(self._path):
                self._path.clear()
                transition = self._transition_after_path
                if transition == "outside":
                    self._enter_outside()
                elif transition == "room":
                    self._enter_room()
                else:
                    self._set_state("idle")
                self._wander_elapsed = 0.0

        elif self._state != "sleep" and self._wander_elapsed >= 9.0:
            self._wander_elapsed = 0.0
            self._start_walk()

    def _apply_behavior_action(self, action_type: ActionType) -> None:
        needs = self.character.needs

        if action_type == ActionType.SLEEP and not self._sleeping:
            self._sleeping = True
            self._path.clear()
            self._set_state("sleep")
            self.speechRequested.emit("Я устала, немного посплю.")
        elif action_type == ActionType.EAT:
            self._path.clear()
            needs.change_hunger(35)
            self._set_state("stand")
            self._temporary_state_time = 1.8
            self.speechRequested.emit("Нашла небольшой перекус!")
            self._emit_needs()
        elif action_type == ActionType.PLAY:
            needs.change_fun(30)
            self._emit_needs()
            if self._state != "walk":
                self._start_walk()
            self.speechRequested.emit("Пойду немного развлекусь!")
        elif action_type == ActionType.WASH:
            self._path.clear()
            needs.change_hygiene(35)
            self._set_state("stand")
            self._temporary_state_time = 2.0
            self.speechRequested.emit("Теперь я чувствую себя чище!")
            self._emit_needs()
        elif action_type == ActionType.TALK:
            needs.change_social(25)
            self._emit_needs()
            self.speechRequested.emit("Мне приятно общаться с тобой!")
        elif action_type == ActionType.RELAX:
            needs.change_comfort(25)
            self._set_state("stand")
            self._temporary_state_time = 2.0
            self._emit_needs()
            self.speechRequested.emit("Немного отдыха — и я снова в порядке.")

    # ========== БАЗА ДАННЫХ ==========

    def _load_from_db(self) -> None:
        """Загружает состояние из БД в персонажа."""
        if not self.db:
            return
        try:
            state = self.db.load_state("mira")
            if state:
                needs = self.character.needs
                needs.energy = state["energy"]
                needs.hunger = state["hunger"]
                needs.fun = state["fun"]
                needs.social = state["social"]
                needs.hygiene = state["hygiene"]
                needs.comfort = state["comfort"]
                self.pet.x = state["pos_x"]
                self.pet.y = state["pos_y"]
                self._scene_mode = state.get("scene_mode", "room")
                if hasattr(self.character.state, "mood"):
                    self.character.state.mood = state.get("mood", "neutral")

            pers = self.db.load_personality("mira")
            if pers:
                p = self.character.personality
                p.friendliness = pers["friendliness"]
                p.curiosity = pers["curiosity"]
                p.laziness = pers["laziness"]
                p.humor = pers["humor"]
                p.chaos = pers["chaos"]
                p.intelligence = pers["intelligence"]
                p.courage = pers["courage"]
                p.backstory = pers["backstory"]
                if hasattr(p, "style"):
                    p.style = pers["style"]
                if hasattr(p, "behavior_style"):
                    p.behavior_style = pers.get("style", "")
                p.likes = pers["likes"]
                p.dislikes = pers["dislikes"]
                p.rules = pers["rules"]

            for m in self.db.load_memories("mira"):
                self.character.memory.memories.append(m)
        except Exception as e:
            print(f"Предупреждение: не удалось загрузить данные из БД: {e}")

    def _save_to_db(self) -> None:
        """Сохраняет текущее состояние персонажа в БД."""
        if not self.db:
            return
        try:
            needs = self.character.needs
            self.db.save_state({
                "energy": needs.energy, "hunger": needs.hunger,
                "fun": needs.fun, "social": needs.social,
                "hygiene": needs.hygiene, "comfort": needs.comfort,
                "pos_x": self.pet.x, "pos_y": self.pet.y,
                "scene_mode": self._scene_mode,
                "mood": getattr(self.character.state, "mood", "neutral"),
            }, "mira")

            p = self.character.personality
            self.db.save_personality({
                "friendliness": p.friendliness,
                "curiosity": p.curiosity,
                "laziness": p.laziness,
                "humor": p.humor,
                "chaos": p.chaos,
                "intelligence": p.intelligence,
                "courage": p.courage,
                "backstory": p.backstory,
                "style": getattr(p, "style",
                                 getattr(p, "behavior_style", "")),
                "likes": p.likes,
                "dislikes": p.dislikes,
                "rules": p.rules,
            }, "mira")

            existing = {m.content
                        for m in self.db.load_memories("mira", limit=2000)}
            for m in self.character.memory.memories:
                if m.content not in existing:
                    self.db.save_memory(m, "mira")

            self.db.touch_character("mira")
        except Exception as e:
            print(f"Предупреждение: не удалось сохранить данные в БД: {e}")

    def close(self) -> None:
        self.timer.stop()
        self._save_to_db()
        self.agent.close()