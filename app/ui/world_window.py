"""Графический интерфейс виртуального мира Chibik."""
from __future__ import annotations

import tkinter as tk

from app.world.navigation import Navigation
from app.world.objects import WorldObject
from app.world.physics import Physics
from app.world.world import World
from app.world.zone import Zone


ROOM_W = 18
ROOM_H = 10
ZONE_NAME = "Комната"

MOVE_STEP = 0.5
PATH_STEP = 1.0
PATH_SUBSTEPS = 5
PATH_INTERVAL_MS = 25


class ChibikWorldWindow:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Chibik — виртуальный мир")
        self.root.geometry("1120x610")
        self.root.minsize(900, 560)
        self.root.configure(bg="#171b24")

        # Создаём мир и игровую зону.
        self.world = World("Chibik")
        self.zone = Zone(
            ZONE_NAME,
            width=ROOM_W,
            height=ROOM_H,
        )
        self.world.add_zone(self.zone)

        # Начальная позиция персонажа.
        self.start_position = (0.5, 3.0)
        self.character = WorldObject(
            x=self.start_position[0],
            y=self.start_position[1],
            width=0.65,
            height=0.75,
            name="Мира",
            solid=True,
        )
        self.world.add_object(ZONE_NAME, self.character)

        # Мебель игрового мира.
        furniture_data = [
            (2, 1, 3, 2, "Кровать", "#7e8fc4", "#d9dff4"),
            (7, 1, 2, 1.2, "Стол", "#b9875a", "#e4bd8f"),
            (12, 1, 1.4, 1.4, "Шкаф", "#a56d50", "#d7a17d"),
            (2, 6, 1.2, 1.2, "Растение", "#578b68", "#9bc99d"),
            (8, 6.5, 2, 1, "Диван", "#c17b83", "#e6b0b5"),
            (14, 6, 1.3, 1.3, "Тумба", "#b9875a", "#e4bd8f"),
        ]

        self.furniture = []

        for x, y, w, h, name, color, detail in furniture_data:
            obj = WorldObject(
                x=x,
                y=y,
                width=w,
                height=h,
                name=name,
                solid=True,
            )
            self.world.add_object(ZONE_NAME, obj)
            self.furniture.append((obj, color, detail))

        # Состояние движения по маршруту.
        self._path: list[tuple[float, float]] = []
        self._path_after_id: str | None = None
        self._path_segment_start: tuple[float, float] | None = None
        self._path_substep = 0

        self.status = tk.StringVar(value="Готов к исследованию")
        self.position = tk.StringVar()
        self.action = tk.StringVar(value="Ожидает команду")

        self._layout()
        self._draw()
        self._update_info()

        # Глобальная привязка позволяет принимать клавиши,
        # даже если фокус находится на другом элементе окна.
        self.root.bind_all("<KeyPress>", self._on_key_press)

        # Устанавливаем фокус после появления окна.
        self.root.after(300, self._focus_canvas)

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _layout(self):
        header = tk.Frame(self.root, bg="#222938", height=54)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header,
            text="CHIBIK",
            font=("Segoe UI", 17, "bold"),
            fg="#f0d9a7",
            bg="#222938",
        ).pack(side="left", padx=22)

        tk.Label(
            header,
            text="ТВОЙ МАЛЕНЬКИЙ МИР",
            font=("Segoe UI", 11),
            fg="#f2f4f8",
            bg="#222938",
        ).pack(side="left", padx=12)

        body = tk.Frame(self.root, bg="#171b24")
        body.pack(fill="both", expand=True, padx=18, pady=18)

        self.canvas = tk.Canvas(
            body,
            bg="#c8d6ad",
            highlightthickness=0,
            takefocus=True,
        )
        self.canvas.pack(side="left", fill="both", expand=True)

        # Щелчок по игровому полю возвращает фокус и задаёт цель.
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.canvas.bind("<Configure>", lambda _event: self._draw())

        side = tk.Frame(body, bg="#222938", width=230)
        side.pack(side="right", fill="y", padx=(16, 0))
        side.pack_propagate(False)

        def label(text, **kwargs):
            padx = kwargs.pop("padx", 16)
            pady = kwargs.pop("pady", (5, 5))
            fg = kwargs.pop("fg", "#f2f4f8")
            font = kwargs.pop("font", ("Segoe UI", 10))

            widget = tk.Label(
                side,
                text=text,
                bg="#222938",
                fg=fg,
                font=font,
                **kwargs,
            )
            widget.pack(anchor="w", padx=padx, pady=pady)
            return widget

        label(
            "ПЕРСОНАЖ",
            fg="#f0d9a7",
            font=("Segoe UI", 11, "bold"),
            pady=(20, 8),
        )
        label("Мира", font=("Segoe UI", 15, "bold"))
        label("Состояние:")
        label("", textvariable=self.status, wraplength=195)

        label(
            "ПОЗИЦИЯ",
            fg="#f0d9a7",
            font=("Segoe UI", 11, "bold"),
            pady=(22, 8),
        )
        label("", textvariable=self.position)

        label(
            "ДЕЙСТВИЕ",
            fg="#f0d9a7",
            font=("Segoe UI", 11, "bold"),
            pady=(22, 8),
        )
        label("", textvariable=self.action, wraplength=195)

        label(
            "УПРАВЛЕНИЕ",
            fg="#f0d9a7",
            font=("Segoe UI", 11, "bold"),
            pady=(22, 8),
        )
        label("W / ↑  — вверх")
        label("S / ↓  — вниз")
        label("A / ←  — влево")
        label("D / →  — вправо")
        label("ЛКМ — идти к точке")

        tk.Button(
            side,
            text="Вернуться в начало",
            command=self._reset_position,
            bg="#3a455a",
            fg="white",
            activebackground="#4b5972",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
        ).pack(fill="x", padx=14, pady=(22, 10))

    def _focus_canvas(self):
        """Передаёт фокус игровому полю."""
        try:
            if self.root.winfo_exists():
                self.root.focus_force()
                self.canvas.focus_set()
        except tk.TclError:
            pass

    def _draw(self):
        """Отрисовывает комнату, мебель и персонажа."""
        if not hasattr(self, "canvas"):
            return

        canvas = self.canvas
        canvas.delete("all")

        width = canvas.winfo_width()
        height = canvas.winfo_height()

        if width < 10 or height < 10:
            return

        cell = min(width / ROOM_W, height / ROOM_H)
        room_width = cell * ROOM_W
        room_height = cell * ROOM_H
        offset_x = (width - room_width) / 2
        offset_y = (height - room_height) / 2

        def rect(x, y, w, h):
            return (
                offset_x + x * cell,
                offset_y + y * cell,
                offset_x + (x + w) * cell,
                offset_y + (y + h) * cell,
            )

        # Пол комнаты.
        canvas.create_rectangle(
            *rect(0, 0, ROOM_W, ROOM_H),
            fill="#c8d6ad",
            outline="#647754",
            width=3,
        )

        # Сетка пола.
        for x in range(ROOM_W + 1):
            px = offset_x + x * cell
            canvas.create_line(
                px,
                offset_y,
                px,
                offset_y + room_height,
                fill="#b3c49a",
            )

        for y in range(ROOM_H + 1):
            py = offset_y + y * cell
            canvas.create_line(
                offset_x,
                py,
                offset_x + room_width,
                py,
                fill="#b3c49a",
            )

        # Мебель.
        for obj, color, detail in self.furniture:
            x1, y1, x2, y2 = rect(
                obj.x,
                obj.y,
                obj.width,
                obj.height,
            )

            canvas.create_rectangle(
                x1 + 3,
                y1 + 3,
                x2 + 3,
                y2 + 3,
                fill="#7f8b72",
                outline="",
            )
            canvas.create_rectangle(
                x1,
                y1,
                x2,
                y2,
                fill=color,
                outline="#574c43",
                width=2,
            )
            canvas.create_rectangle(
                x1 + 4,
                y1 + 4,
                x2 - 4,
                y2 - 4,
                outline=detail,
                width=2,
            )
            canvas.create_text(
                (x1 + x2) / 2,
                (y1 + y2) / 2,
                text=obj.name,
                fill="white",
                font=("Segoe UI", max(7, int(cell * 0.22)), "bold"),
            )

        # Персонаж.
        x1, y1, x2, y2 = rect(
            self.character.x,
            self.character.y,
            self.character.width,
            self.character.height,
        )

        canvas.create_oval(
            x1,
            y1,
            x2,
            y2,
            fill="#e6b95f",
            outline="#75562d",
            width=2,
        )

        eye_size = max(2, cell * 0.08)

        for eye_x in (
            x1 + (x2 - x1) * 0.3,
            x1 + (x2 - x1) * 0.7,
        ):
            canvas.create_oval(
                eye_x - eye_size / 2,
                y1 + (y2 - y1) * 0.3,
                eye_x + eye_size / 2,
                y1 + (y2 - y1) * 0.3 + eye_size,
                fill="#292a35",
                outline="",
            )

        canvas.create_text(
            (x1 + x2) / 2,
            y2 + 12,
            text="Мира",
            fill="#293326",
            font=("Segoe UI", 9, "bold"),
        )

    def _on_key_press(self, event):
        """Обрабатывает WASD, русскую раскладку и стрелки."""
        key = event.keysym.lower()
        char = (event.char or "").lower()

        movements = {
            "w": (0, -MOVE_STEP),
            "ц": (0, -MOVE_STEP),
            "s": (0, MOVE_STEP),
            "ы": (0, MOVE_STEP),
            "a": (-MOVE_STEP, 0),
            "ф": (-MOVE_STEP, 0),
            "d": (MOVE_STEP, 0),
            "в": (MOVE_STEP, 0),
            "up": (0, -MOVE_STEP),
            "down": (0, MOVE_STEP),
            "left": (-MOVE_STEP, 0),
            "right": (MOVE_STEP, 0),
        }

        delta = movements.get(key)

        if delta is None:
            delta = movements.get(char)

        if delta is None:
            return None

        # Ручное движение прерывает маршрут мыши.
        self._cancel_path()
        self._move(*delta)

        return "break"

    def _move(self, dx: float, dy: float):
        """Перемещает персонажа с проверкой столкновений."""
        moved = Physics.move(
            self.character,
            self.zone,
            dx,
            dy,
        )

        if moved:
            self.action.set("Персонаж перемещён")
            self.status.set("Исследует комнату")
        else:
            self.action.set("Путь заблокирован")
            self.status.set("Столкновение или граница комнаты")

        self._draw()
        self._update_info()

    def _on_canvas_click(self, event):
        """Преобразует клик мыши в цель для навигации."""
        self.canvas.focus_set()
        self._cancel_path()

        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()

        if width < 10 or height < 10:
            return

        cell = min(width / ROOM_W, height / ROOM_H)
        offset_x = (width - cell * ROOM_W) / 2
        offset_y = (height - cell * ROOM_H) / 2

        clicked_x = (event.x - offset_x) / cell
        clicked_y = (event.y - offset_y) / cell

        # Клик вне комнаты не задаёт маршрут.
        if not (0 <= clicked_x < ROOM_W and 0 <= clicked_y < ROOM_H):
            self.status.set("Выберите точку внутри комнаты")
            return

        # Привязываем цель к сетке относительно текущего положения.
        target_x = self.character.x + round(
            (clicked_x - self.character.x) / PATH_STEP
        ) * PATH_STEP
        target_y = self.character.y + round(
            (clicked_y - self.character.y) / PATH_STEP
        ) * PATH_STEP

        # Цель должна оставаться внутри комнаты с учётом размера Миры.
        target_x = max(
            self.zone.x,
            min(target_x, self.zone.x + self.zone.width - self.character.width),
        )
        target_y = max(
            self.zone.y,
            min(target_y, self.zone.y + self.zone.height - self.character.height),
        )

        self._start_path(target_x, target_y)

    def _start_path(self, target_x: float, target_y: float):
        """Находит и запускает маршрут к указанной позиции."""
        self._cancel_path()

        try:
            path = Navigation.find_path(
                obj=self.character,
                zone=self.zone,
                target_x=target_x,
                target_y=target_y,
                step=PATH_STEP,
            )
        except (ValueError, TypeError) as error:
            self.status.set(f"Не удалось построить маршрут: {error}")
            self.action.set("Ошибка навигации")
            return

        if not path:
            self.status.set("До этой точки нет свободного пути")
            self.action.set("Маршрут недоступен")
            return

        self._path = path[1:]

        if not self._path:
            self.status.set("Мира уже находится в этой точке")
            self.action.set("Ожидает команду")
            return

        self._path_segment_start = (
            self.character.x,
            self.character.y,
        )
        self._path_substep = 0

        self.status.set("Мира идёт к указанной точке")
        self.action.set("Движение по маршруту")
        self._advance_path()

    def _advance_path(self):
        """Плавно перемещает персонажа по рассчитанному маршруту."""
        self._path_after_id = None

        if not self._path or self._path_segment_start is None:
            return

        target_x, target_y = self._path[0]
        start_x, start_y = self._path_segment_start

        self._path_substep += 1
        fraction = self._path_substep / PATH_SUBSTEPS

        desired_x = start_x + (target_x - start_x) * fraction
        desired_y = start_y + (target_y - start_y) * fraction

        moved = Physics.move(
            self.character,
            self.zone,
            desired_x - self.character.x,
            desired_y - self.character.y,
        )

        if not moved:
            self._cancel_path()
            self.status.set("Движение остановлено препятствием")
            self.action.set("Маршрут прерван")
            self._draw()
            self._update_info()
            return

        if self._path_substep >= PATH_SUBSTEPS:
            self._path.pop(0)
            self._path_segment_start = (
                self.character.x,
                self.character.y,
            )
            self._path_substep = 0

        self._draw()
        self._update_info()

        if self._path:
            self._path_after_id = self.root.after(
                PATH_INTERVAL_MS,
                self._advance_path,
            )
        else:
            self.status.set("Мира пришла к цели")
            self.action.set("Прибыла в точку назначения")

    def _cancel_path(self):
        """Безопасно отменяет автоматическое движение."""
        if self._path_after_id is not None:
            try:
                self.root.after_cancel(self._path_after_id)
            except tk.TclError:
                pass

        self._path_after_id = None
        self._path = []
        self._path_segment_start = None
        self._path_substep = 0

    def _reset_position(self):
        """Строит маршрут к начальной позиции."""
        self._start_path(
            self.start_position[0],
            self.start_position[1],
        )

    def _update_info(self):
        self.position.set(
            f"X: {self.character.x:.1f}   Y: {self.character.y:.1f}"
        )

    def _on_close(self):
        """Отменяет запланированные события перед закрытием."""
        self._cancel_path()
        self.root.destroy()


def launch():
    root = tk.Tk()
    ChibikWorldWindow(root)
    root.mainloop()


if __name__ == "__main__":
    launch()