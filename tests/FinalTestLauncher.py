import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional

from app.ai.agent import Agent
from app.ai.llm import LocalLLM
from app.ai.planner import Planner
from app.character.character import Character
from app.voice.voice_manager import VoiceManager

from tests.character_database import CharacterDatabase


class CharacterLauncher:

    def __init__(self):
        self.database = CharacterDatabase()

        self.root = tk.Tk()

        self.root.title("Desktop Pet — Character Manager")
        self.root.geometry("900x600")
        self.root.minsize(800, 500)

        self.selected_character_id: Optional[str] = None
        self.voice_manager: Optional[VoiceManager] = None
        self.agent: Optional[Agent] = None
        self.character: Optional[Character] = None

        self.build_interface()
        self.refresh_characters()

        self.root.protocol(
            "WM_DELETE_WINDOW",
            self.on_close
        )

    # =========================================================
    # GUI
    # =========================================================

    def build_interface(self):

        main = ttk.Frame(self.root, padding=20)
        main.pack(fill=tk.BOTH, expand=True)

        title = ttk.Label(
            main,
            text="DESKTOP PET",
            font=("Segoe UI", 22, "bold")
        )

        title.pack(anchor=tk.W)

        subtitle = ttk.Label(
            main,
            text="Выберите персонажа для запуска",
            font=("Segoe UI", 11)
        )

        subtitle.pack(
            anchor=tk.W,
            pady=(0, 20)
        )

        content = ttk.Frame(main)
        content.pack(
            fill=tk.BOTH,
            expand=True
        )

        # -----------------------------------------------------
        # Список персонажей
        # -----------------------------------------------------

        left = ttk.LabelFrame(
            content,
            text="Персонажи",
            padding=10
        )

        left.pack(
            side=tk.LEFT,
            fill=tk.BOTH,
            expand=True
        )

        self.character_list = tk.Listbox(
            left,
            font=("Segoe UI", 12),
            activestyle="none"
        )

        self.character_list.pack(
            fill=tk.BOTH,
            expand=True
        )

        self.character_list.bind(
            "<<ListboxSelect>>",
            self.on_character_select
        )

        # -----------------------------------------------------
        # Информация
        # -----------------------------------------------------

        right = ttk.LabelFrame(
            content,
            text="Информация",
            padding=20
        )

        right.pack(
            side=tk.RIGHT,
            fill=tk.BOTH,
            expand=True,
            padx=(20, 0)
        )

        self.info_name = ttk.Label(
            right,
            text="Персонаж не выбран",
            font=("Segoe UI", 18, "bold")
        )

        self.info_name.pack(
            anchor=tk.W,
            pady=(0, 10)
        )

        self.info_age = ttk.Label(
            right,
            text=""
        )

        self.info_age.pack(
            anchor=tk.W
        )

        self.info_traits = ttk.Label(
            right,
            text="",
            wraplength=300,
            justify=tk.LEFT
        )

        self.info_traits.pack(
            anchor=tk.W,
            pady=(15, 0)
        )

        self.info_backstory = ttk.Label(
            right,
            text="",
            wraplength=300,
            justify=tk.LEFT
        )

        self.info_backstory.pack(
            anchor=tk.W,
            pady=(15, 0)
        )

        # -----------------------------------------------------
        # Кнопки
        # -----------------------------------------------------

        buttons = ttk.Frame(main)
        buttons.pack(
            fill=tk.X,
            pady=(20, 0)
        )

        self.create_button = ttk.Button(
            buttons,
            text="Создать",
            command=self.create_character
        )

        self.create_button.pack(
            side=tk.LEFT,
            padx=(0, 10)
        )

        self.edit_button = ttk.Button(
            buttons,
            text="Редактировать",
            command=self.edit_character
        )

        self.edit_button.pack(
            side=tk.LEFT,
            padx=(0, 10)
        )

        self.delete_button = ttk.Button(
            buttons,
            text="Удалить",
            command=self.delete_character
        )

        self.delete_button.pack(
            side=tk.LEFT
        )

        self.start_button = ttk.Button(
            buttons,
            text="▶ Запустить",
            command=self.start_character
        )

        self.start_button.pack(
            side=tk.RIGHT
        )

    # =========================================================
    # Работа со списком
    # =========================================================

    def refresh_characters(self):

        self.character_list.delete(
            0,
            tk.END
        )

        characters = self.database.list_characters()

        self.characters = characters

        for character in characters:

            self.character_list.insert(
                tk.END,
                f"{character['name']}   |   {character['age']} лет"
            )

        self.selected_character_id = None

        self.clear_info()

    def on_character_select(self, event=None):

        selection = self.character_list.curselection()

        if not selection:
            return

        index = selection[0]

        character_info = self.characters[index]

        self.selected_character_id = character_info["id"]

        character = self.database.load_character_by_id(
            self.selected_character_id
        )

        if character is None:
            return

        self.show_character_info(character)

    def show_character_info(
        self,
        character: Character
    ):

        self.info_name.config(
            text=character.name
        )

        self.info_age.config(
            text=f"Возраст: {character.age}"
        )

        personality = character.personality

        traits = personality.traits

        if traits:
            traits_text = (
                "Черты характера:\n"
                + ", ".join(traits)
            )
        else:
            traits_text = (
                "Черты характера:\nне заданы"
            )

        self.info_traits.config(
            text=traits_text
        )

        if personality.backstory:
            backstory = (
                "Предыстория:\n"
                + personality.backstory
            )
        else:
            backstory = (
                "Предыстория:\nне задана"
            )

        self.info_backstory.config(
            text=backstory
        )

    def clear_info(self):

        self.info_name.config(
            text="Персонаж не выбран"
        )

        self.info_age.config(
            text=""
        )

        self.info_traits.config(
            text=""
        )

        self.info_backstory.config(
            text=""
        )

    # =========================================================
    # Создание
    # =========================================================

    def create_character(self):

        window = CharacterEditorWindow(
            parent=self.root,
            character=None,
            on_save=self.on_character_saved
        )

        window.show()

    # =========================================================
    # Редактирование
    # =========================================================

    def edit_character(self):

        if not self.selected_character_id:

            messagebox.showwarning(
                "Персонаж",
                "Сначала выберите персонажа."
            )

            return

        character = self.database.load_character_by_id(
            self.selected_character_id
        )

        if character is None:

            messagebox.showerror(
                "Ошибка",
                "Не удалось загрузить персонажа."
            )

            return

        window = CharacterEditorWindow(
            parent=self.root,
            character=character,
            on_save=self.on_character_saved
        )

        window.show()

    # =========================================================
    # Сохранение
    # =========================================================

    def on_character_saved(
        self,
        character: Character
    ):

        self.database.save_character(
            character
        )

        self.refresh_characters()

        messagebox.showinfo(
            "Готово",
            f"Персонаж «{character.name}» сохранён."
        )

    # =========================================================
    # Удаление
    # =========================================================

    def delete_character(self):

        if not self.selected_character_id:

            messagebox.showwarning(
                "Персонаж",
                "Сначала выберите персонажа."
            )

            return

        character = self.database.load_character_by_id(
            self.selected_character_id
        )

        if character is None:
            return

        result = messagebox.askyesno(
            "Удаление",
            f"Удалить персонажа «{character.name}»?"
        )

        if not result:
            return

        self.database.delete_character(
            self.selected_character_id
        )

        self.refresh_characters()

        messagebox.showinfo(
            "Готово",
            "Персонаж удалён."
        )

    # =========================================================
    # Запуск AI
    # =========================================================

    def start_character(self):

        if not self.selected_character_id:

            messagebox.showwarning(
                "Запуск",
                "Сначала выберите персонажа."
            )

            return

        character = self.database.load_character_by_id(
            self.selected_character_id
        )

        if character is None:

            messagebox.showerror(
                "Ошибка",
                "Не удалось загрузить персонажа."
            )

            return

        self.character = character

        try:

            llm = LocalLLM()

            planner = Planner()

            self.agent = Agent(
                character=self.character,
                llm=llm,
                planner=planner,
                memory=self.character.memory,
                interaction_saver=(
                    self.database.save_interaction
                ),
                memory_saver=(
                    self.database.save_memory
                ),
                character_saver=(
                    self.database.save_character
                )
            )

        except Exception as error:

            messagebox.showerror(
                "Ошибка AI",
                str(error)
            )

            return

        self.open_ai_window()

    # =========================================================
    # AI окно
    # =========================================================

    def open_ai_window(self):

        window = tk.Toplevel(
            self.root
        )

        window.title(
            f"Desktop Pet — {self.character.name}"
        )

        window.geometry(
            "700x600"
        )

        window.protocol(
            "WM_DELETE_WINDOW",
            lambda: self.stop_ai_window(window)
        )

        # -----------------------------------------------------
        # Заголовок
        # -----------------------------------------------------

        title = ttk.Label(
            window,
            text=self.character.name,
            font=("Segoe UI", 20, "bold")
        )

        title.pack(
            pady=(15, 5)
        )

        status = ttk.Label(
            window,
            text="AI готов. Запустите голосовой ввод.",
            font=("Segoe UI", 10)
        )

        status.pack(
            pady=(0, 10)
        )

        # -----------------------------------------------------
        # Чат
        # -----------------------------------------------------

        chat_frame = ttk.Frame(
            window,
            padding=10
        )

        chat_frame.pack(
            fill=tk.BOTH,
            expand=True
        )

        chat = tk.Text(
            chat_frame,
            state=tk.DISABLED,
            wrap=tk.WORD,
            font=("Segoe UI", 11)
        )

        chat.pack(
            fill=tk.BOTH,
            expand=True
        )

        # -----------------------------------------------------
        # Функция добавления сообщения
        # -----------------------------------------------------

        def add_message(
            speaker: str,
            message: str
        ):

            chat.config(
                state=tk.NORMAL
            )

            chat.insert(
                tk.END,
                f"{speaker}:\n"
            )

            chat.insert(
                tk.END,
                f"{message}\n\n"
            )

            chat.see(
                tk.END
            )

            chat.config(
                state=tk.DISABLED
            )

        # -----------------------------------------------------
        # Голос
        # -----------------------------------------------------

        def process_voice_message(
            text: str
        ):

            if not text:
                return

            add_message(
                "Вы",
                text
            )

            status.config(
                text="Qwen думает..."
            )

            try:

                response = self.agent.chat(
                    text
                )

                add_message(
                    self.character.name,
                    response
                )

                status.config(
                    text="Готов к следующей команде."
                )

            except Exception as error:

                add_message(
                    "Ошибка",
                    str(error)
                )

                status.config(
                    text="Ошибка AI."
                )

        # -----------------------------------------------------
        # Кнопки
        # -----------------------------------------------------

        controls = ttk.Frame(
            window,
            padding=10
        )

        controls.pack(
            fill=tk.X
        )

        def start_voice():

            if self.voice_manager is not None:
                return

            try:

                self.voice_manager = VoiceManager(
                    on_text=process_voice_message
                )

                self.voice_manager.start()

                status.config(
                    text="🎤 Голосовой ввод активен. Говорите."
                )

                voice_button.config(
                    text="🎤 Голос активен"
                )

            except Exception as error:

                self.voice_manager = None

                messagebox.showerror(
                    "Ошибка голоса",
                    str(error),
                    parent=window
                )

        def stop_voice():

            if self.voice_manager:

                self.voice_manager.stop()

                self.voice_manager = None

            status.config(
                text="Голосовой ввод остановлен."
            )

            voice_button.config(
                text="🎤 Запустить голос"
            )

        voice_button = ttk.Button(
            controls,
            text="🎤 Запустить голос",
            command=start_voice
        )

        voice_button.pack(
            side=tk.LEFT,
            padx=(0, 10)
        )

        stop_button = ttk.Button(
            controls,
            text="Остановить голос",
            command=stop_voice
        )

        stop_button.pack(
            side=tk.LEFT
        )

        close_button = ttk.Button(
            controls,
            text="Закрыть",
            command=lambda: self.stop_ai_window(window)
        )

        close_button.pack(
            side=tk.RIGHT
        )

        # -----------------------------------------------------
        # Первое сообщение
        # -----------------------------------------------------

        add_message(
            self.character.name,
            (
                f"Привет! Я {self.character.name}. "
                "Можешь говорить со мной через микрофон."
            )
        )

    # =========================================================
    # Остановка AI
    # =========================================================

    def stop_ai_window(
        self,
        window
    ):

        if self.voice_manager:

            self.voice_manager.stop()

            self.voice_manager = None

        window.destroy()

    # =========================================================
    # Закрытие приложения
    # =========================================================

    def on_close(self):

        if self.voice_manager:

            self.voice_manager.stop()

            self.voice_manager = None

        self.root.destroy()

    # =========================================================
    # Запуск
    # =========================================================

    def run(self):

        self.root.mainloop()


# =============================================================
# Редактор персонажа
# =============================================================

class CharacterEditorWindow:

    def __init__(
        self,
        parent,
        character: Optional[Character],
        on_save
    ):

        self.parent = parent
        self.character = character
        self.on_save = on_save

        self.window = tk.Toplevel(
            parent
        )

        if character is None:
            self.window.title(
                "Создание персонажа"
            )
        else:
            self.window.title(
                f"Редактирование — {character.name}"
            )

        self.window.geometry(
            "700x750"
        )

        self.window.transient(
            parent
        )

        self.window.grab_set()

        self.build()

    def build(self):

        main = ttk.Frame(
            self.window,
            padding=20
        )

        main.pack(
            fill=tk.BOTH,
            expand=True
        )

        # -----------------------------------------------------
        # Основная информация
        # -----------------------------------------------------

        basic = ttk.LabelFrame(
            main,
            text="Основная информация",
            padding=10
        )

        basic.pack(
            fill=tk.X
        )

        ttk.Label(
            basic,
            text="Имя:"
        ).grid(
            row=0,
            column=0,
            sticky=tk.W,
            pady=5
        )

        self.name_var = tk.StringVar(
            value=(
                self.character.name
                if self.character
                else ""
            )
        )

        ttk.Entry(
            basic,
            textvariable=self.name_var,
            width=40
        ).grid(
            row=0,
            column=1,
            sticky=tk.W,
            padx=10
        )

        ttk.Label(
            basic,
            text="Возраст:"
        ).grid(
            row=1,
            column=0,
            sticky=tk.W,
            pady=5
        )

        self.age_var = tk.IntVar(
            value=(
                self.character.age
                if self.character
                else 20
            )
        )

        ttk.Spinbox(
            basic,
            from_=1,
            to=150,
            textvariable=self.age_var,
            width=10
        ).grid(
            row=1,
            column=1,
            sticky=tk.W,
            padx=10
        )

        # -----------------------------------------------------
        # Личность
        # -----------------------------------------------------

        personality = ttk.LabelFrame(
            main,
            text="Личность",
            padding=10
        )

        personality.pack(
            fill=tk.X,
            pady=15
        )

        self.traits = {}

        trait_names = [
            ("Дружелюбие", "friendliness"),
            ("Любопытство", "curiosity"),
            ("Лень", "laziness"),
            ("Юмор", "humor"),
            ("Хаотичность", "chaos"),
            ("Интеллект", "intelligence"),
            ("Смелость", "bravery"),
        ]

        for row, (label, attribute) in enumerate(
            trait_names
        ):

            ttk.Label(
                personality,
                text=label
            ).grid(
                row=row,
                column=0,
                sticky=tk.W,
                pady=3
            )

            value = (
                getattr(
                    self.character.personality,
                    attribute
                )
                if self.character
                else 50
            )

            variable = tk.DoubleVar(
                value=value
            )

            self.traits[attribute] = variable

            ttk.Scale(
                personality,
                from_=0,
                to=100,
                variable=variable,
                orient=tk.HORIZONTAL,
                length=250
            ).grid(
                row=row,
                column=1,
                padx=10
            )

            value_label = ttk.Label(
                personality,
                textvariable=variable
            )

            value_label.grid(
                row=row,
                column=2
            )

        # -----------------------------------------------------
        # Предыстория
        # -----------------------------------------------------

        ttk.Label(
            main,
            text="Предыстория:"
        ).pack(
            anchor=tk.W
        )

        self.backstory = tk.Text(
            main,
            height=5,
            wrap=tk.WORD
        )

        self.backstory.pack(
            fill=tk.X,
            pady=(5, 15)
        )

        if self.character:
            self.backstory.insert(
                "1.0",
                self.character.personality.backstory
            )

        # -----------------------------------------------------
        # Стиль поведения
        # -----------------------------------------------------

        ttk.Label(
            main,
            text="Стиль поведения:"
        ).pack(
            anchor=tk.W
        )

        self.behavior_style = tk.Text(
            main,
            height=4,
            wrap=tk.WORD
        )

        self.behavior_style.pack(
            fill=tk.X,
            pady=(5, 15)
        )

        if self.character:
            self.behavior_style.insert(
                "1.0",
                self.character.personality.behavior_style
            )

        # -----------------------------------------------------
        # Сохранение
        # -----------------------------------------------------

        buttons = ttk.Frame(
            main
        )

        buttons.pack(
            fill=tk.X,
            pady=(10, 0)
        )

        ttk.Button(
            buttons,
            text="Отмена",
            command=self.window.destroy
        ).pack(
            side=tk.RIGHT,
            padx=(10, 0)
        )

        ttk.Button(
            buttons,
            text="Сохранить",
            command=self.save
        ).pack(
            side=tk.RIGHT
        )

    def save(self):

        name = self.name_var.get().strip()

        if not name:

            messagebox.showwarning(
                "Ошибка",
                "Введите имя персонажа.",
                parent=self.window
            )

            return

        try:

            age = int(
                self.age_var.get()
            )

        except ValueError:

            messagebox.showwarning(
                "Ошибка",
                "Возраст должен быть числом.",
                parent=self.window
            )

            return

        if self.character is None:

            character = Character(
                name=name,
                age=age
            )

        else:

            character = self.character

            character.name = name
            character.age = age

        # -----------------------------------------------------
        # Personality
        # -----------------------------------------------------

        for attribute, variable in self.traits.items():

            setattr(
                character.personality,
                attribute,
                float(
                    variable.get()
                )
            )

        character.personality.backstory = (
            self.backstory
            .get(
                "1.0",
                tk.END
            )
            .strip()
        )

        character.personality.behavior_style = (
            self.behavior_style
            .get(
                "1.0",
                tk.END
            )
            .strip()
        )

        self.on_save(
            character
        )

        self.window.destroy()

    def show(self):

        self.window.wait_window()


# =============================================================
# ENTRY POINT
# =============================================================

if __name__ == "__main__":

    launcher = CharacterLauncher()

    launcher.run()