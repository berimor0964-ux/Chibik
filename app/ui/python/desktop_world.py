"""Связка экранного питомца с моделью World/Zone/Physics/Navigation."""
from __future__ import annotations

import math
import random

from PySide6.QtCore import QObject, QTimer, Signal
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
    """Инструмент AI для перемещения питомца по сетке рабочего стола."""

    name = "desktop_walk"
    description = (
        "Переместить Миру в другую точку рабочего стола. Координаты x и y "
        "измеряются клетками по 32 пикселя от левого верхнего угла доступной области. "
        "Используй только координаты в пределах размеров экрана."
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
            return {"status": "rejected", "reason": "Координаты за границами рабочего стола", "max_x": max_x, "max_y": max_y}
        self.controller.walkRequested.emit(x, y)
        return {"status": "movement_requested", "x": x, "y": y}


class DesktopWorldController(QObject):
    """Мир размером с доступную область экрана; координаты хранятся в World."""

    positionChanged = Signal(int, int)
    stateChanged = Signal(str, str)
    speechRequested = Signal(str)
    needsChanged = Signal(float, float, float)
    walkRequested = Signal(int, int)

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            raise RuntimeError("Не удалось определить экран для Desktop Pet.")
        self.geometry = screen.availableGeometry()
        self.grid_width = max(8, self.geometry.width() // CELL_SIZE)
        self.grid_height = max(8, self.geometry.height() // CELL_SIZE)

        self.world = World("Рабочий стол")
        self.zone = Zone(
            "Рабочий стол",
            width=float(self.grid_width),
            height=float(self.grid_height),
        )
        self.world.add_zone(self.zone)
        self.pet = WorldObject(
            x=float(self.grid_width - 4),
            y=float(self.grid_height - 4),
            width=4.0,
            height=4.0,
            solid=True,
            name="Мира",
        )
        self.world.add_object(self.zone.name, self.pet)

        self.character = Character(name="Мира", age=1)
        self.agent = self._create_agent(self.character)
        self.walkRequested.connect(self.request_walk_to)
        self.agent.tools["desktop_walk"] = DesktopWalkTool(self)
        self._path: list[tuple[float, float]] = []
        self._path_index = 0
        self._paused = False
        self._state = "idle"
        self._direction = "right"
        self._elapsed = 0.0
        self._needs_elapsed = 0.0
        self._behavior_elapsed = 0.0
        self._wander_elapsed = 0.0
        self._sleeping = False
        self._temporary_state_time = 0.0
        self._random = random.Random()

        self.timer = QTimer(self)
        self.timer.setInterval(16)  # около 60 обновлений в секунду
        self.timer.timeout.connect(self.tick)
        self.timer.start()
        QTimer.singleShot(0, self._emit_position)
        self._emit_state()
        self._emit_needs()

    @staticmethod
    def _create_agent(character: Character) -> Agent:
        """MockLLM работает сразу; LocalLLM включается через CHIBIK_LLM=local."""
        import os
        mode = os.getenv("CHIBIK_LLM")
        if mode is None:
            mode = "local" if os.getenv("LOCAL_LLM_URL") else "mock"
        llm = LocalLLM() if mode.lower() == "local" else MockLLM()
        return Agent(character=character, llm=llm, planner=Planner())

    @property
    def state(self) -> str:
        return self._state

    @property
    def direction(self) -> str:
        return self._direction

    def _emit_position(self) -> None:
        x = self.geometry.x() + round(self.pet.x * CELL_SIZE)
        y = self.geometry.y() + round(self.pet.y * CELL_SIZE)
        self.positionChanged.emit(x, y)

    def _emit_state(self) -> None:
        self.stateChanged.emit(self._state, self._direction)

    def _emit_needs(self) -> None:
        needs = self.character.needs
        self.needsChanged.emit(float(needs.energy), float(needs.hunger), float(needs.fun))

    def pause(self) -> None:
        self._paused = True

    def resume(self) -> None:
        self._paused = False

    def set_window_position(self, x: int, y: int) -> None:
        """Синхронизирует ручное перетаскивание с моделью мира."""
        gx = (x - self.geometry.x()) / CELL_SIZE
        gy = (y - self.geometry.y()) / CELL_SIZE
        gx = min(max(0.0, gx), self.zone.width - self.pet.width)
        gy = min(max(0.0, gy), self.zone.height - self.pet.height)
        self.pet.x, self.pet.y = gx, gy
        self._path.clear()
        self._path_index = 0
        self._set_state("idle")
        self._emit_position()

    def _set_state(self, state: str) -> None:
        if self._state != state:
            self._state = state
            self.character.state.current_action = state
            self._emit_state()

    def _start_walk(self, target_x: int | None = None, target_y: int | None = None) -> bool:
        max_x = max(0, self.grid_width - int(self.pet.width))
        max_y = max(0, self.grid_height - int(self.pet.height))
        if target_x is None:
            target_x = self._random.randint(0, max_x)
        if target_y is None:
            target_y = self._random.randint(0, max_y)
        start = (round(self.pet.x), round(self.pet.y))
        target = (float(min(max_x, max(0, target_x))), float(min(max_y, max(0, target_y))))
        # A* принимает узлы сетки. Приводим текущую позицию к ближайшей клетке.
        if abs(self.pet.x - start[0]) > 1e-6 or abs(self.pet.y - start[1]) > 1e-6:
            self.pet.x, self.pet.y = float(start[0]), float(start[1])
            self._emit_position()
        path = Navigation.find_path(self.pet, self.zone, target[0], target[1], step=1.0)
        if not path:
            return False
        self._path = path
        self._path_index = 1
        if len(path) <= 1:
            self._set_state("idle")
            return False
        self._set_state("walk")
        return True

    def request_walk(self) -> None:
        self._sleeping = False
        self._start_walk()

    def request_walk_to(self, x: int, y: int) -> None:
        """Слот для безопасного вызова перемещения из потока AI."""
        self._sleeping = False
        if not self._start_walk(int(x), int(y)):
            self.speechRequested.emit("Я не смогла найти безопасный путь туда.")

    def perform_action(self, action: str) -> str:
        action = (action or "").lower()
        needs = self.character.needs
        if action in ("walk", "explore"):
            self.request_walk()
            self.speechRequested.emit("Пойду немного прогуляюсь!")
        elif action == "sleep":
            self._path.clear()
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
                f"Энергия: {needs.energy:.0f}%, голод: {needs.hunger:.0f}%, веселье: {needs.fun:.0f}%"
            )
        elif action == "memory":
            memories = self.character.memory.get_recent(limit=1)
            self.speechRequested.emit(memories[-1].content if memories else "Мы пока только знакомимся!")
        elif action == "talk":
            self.speechRequested.emit("Я здесь! Напиши мне в чате.")
        elif action == "settings":
            return "settings"
        elif action == "quit":
            return "quit"
        self._emit_needs()
        return action

    def answer_chat(self, message: str) -> str:
        return self.agent.chat(message)

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
            action = self.agent.update()
            if action:
                self._apply_behavior_action(action.type)

        if self._temporary_state_time > 0:
            self._temporary_state_time = max(0.0, self._temporary_state_time - dt)
            if self._temporary_state_time == 0 and self._state == "stand":
                self._set_state("idle")

        if self._state == "walk" and self._path_index < len(self._path):
            target_x, target_y = self._path[self._path_index]
            dx, dy = target_x - self.pet.x, target_y - self.pet.y
            distance = math.hypot(dx, dy)
            step = 2.8 * dt  # скорость в клетках в секунду
            if distance <= step or distance < 1e-5:
                nx, ny = target_x, target_y
                self._path_index += 1
            else:
                nx = self.pet.x + dx / distance * step
                ny = self.pet.y + dy / distance * step
            if Physics.can_move(self.pet, self.zone, nx, ny):
                self.pet.x, self.pet.y = nx, ny
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
                self._set_state("idle")
                self._wander_elapsed = 0.0
        elif self._state != "sleep" and self._wander_elapsed >= 9.0:
            self._wander_elapsed = 0.0
            self._start_walk()


    def _apply_behavior_action(self, action_type: ActionType) -> None:
        """Исполняет решение Behavior в модели мира, а не только меняет подпись."""
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

    def close(self) -> None:
        self.timer.stop()
        self.agent.close()
