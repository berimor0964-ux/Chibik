import sqlite3
import tkinter as tk

from pathlib import Path
from tkinter import ttk, messagebox

from app.character.character import Character

from tests.character_database import CharacterDatabase

BASE_DIR = Path(__file__).resolve().parent
DATABASE_FILE = BASE_DIR / "character_data.db"


class CharacterEditor:
    def __init__(self, root):
        self.root = root

        self.root.title("Desktop Pet — Character Editor")
        self.root.geometry("900x850")
        self.root.minsize(800, 700)

        self.database = CharacterDatabase(DATABASE_FILE)

        self.character = (
            self.database.load_character()
            or Character(
                name="Мира",
                age=21
            )
        )

        self.create_interface()
        self.load_character_to_interface()

    # ---------------------------------------------------------
    # UI
    # ---------------------------------------------------------

    def create_interface(self):

        main = ttk.Frame(self.root, padding=15)
        main.pack(fill="both", expand=True)

        title = ttk.Label(
            main,
            text="Настройка персонажа",
            font=("Segoe UI", 18, "bold")
        )

        title.pack(anchor="w", pady=(0, 15))

        notebook = ttk.Notebook(main)
        notebook.pack(fill="both", expand=True)

        self.general_tab = ttk.Frame(notebook, padding=15)
        self.personality_tab = ttk.Frame(notebook, padding=15)
        self.story_tab = ttk.Frame(notebook, padding=15)

        notebook.add(
            self.general_tab,
            text="Основное"
        )

        notebook.add(
            self.personality_tab,
            text="Характер"
        )

        notebook.add(
            self.story_tab,
            text="История"
        )

        self.create_general_tab()
        self.create_personality_tab()
        self.create_story_tab()

        buttons = ttk.Frame(main)
        buttons.pack(fill="x", pady=(15, 0))

        ttk.Button(
            buttons,
            text="Применить и сохранить",
            command=self.save_character
        ).pack(
            side="left",
            padx=(0, 10)
        )

        ttk.Button(
            buttons,
            text="Загрузить из базы",
            command=self.reload_character
        ).pack(
            side="left",
            padx=(0, 10)
        )

        ttk.Button(
            buttons,
            text="Показать настройки",
            command=self.show_character
        ).pack(
            side="left",
            padx=(0, 10)
        )

        ttk.Button(
            buttons,
            text="Очистить историю",
            command=self.clear_history
        ).pack(
            side="right"
        )

    # ---------------------------------------------------------
    # General
    # ---------------------------------------------------------

    def create_general_tab(self):

        frame = self.general_tab

        ttk.Label(
            frame,
            text="Имя персонажа"
        ).pack(anchor="w")

        self.name_var = tk.StringVar()

        ttk.Entry(
            frame,
            textvariable=self.name_var,
            width=50
        ).pack(
            fill="x",
            pady=(5, 15)
        )

        ttk.Label(
            frame,
            text="Возраст"
        ).pack(anchor="w")

        self.age_var = tk.IntVar()

        ttk.Spinbox(
            frame,
            from_=1,
            to=200,
            textvariable=self.age_var,
            width=10
        ).pack(
            anchor="w",
            pady=(5, 15)
        )

    # ---------------------------------------------------------
    # Personality
    # ---------------------------------------------------------

    def create_personality_tab(self):

        frame = self.personality_tab

        self.sliders = {}

        personality_fields = [
            ("friendliness", "Дружелюбие"),
            ("curiosity", "Любопытство"),
            ("laziness", "Лень"),
            ("humor", "Юмор"),
            ("chaos", "Хаотичность"),
            ("intelligence", "Интеллект"),
            ("bravery", "Смелость"),
        ]

        for field_name, title in personality_fields:

            row = ttk.Frame(frame)
            row.pack(
                fill="x",
                pady=5
            )

            ttk.Label(
                row,
                text=title,
                width=20
            ).pack(side="left")

            variable = tk.DoubleVar()

            scale = ttk.Scale(
                row,
                from_=0,
                to=100,
                variable=variable,
                orient="horizontal"
            )

            scale.pack(
                side="left",
                fill="x",
                expand=True,
                padx=10
            )

            value_label = ttk.Label(
                row,
                text="50"
            )

            value_label.pack(
                side="right",
                padx=10
            )

            variable.trace_add(
                "write",
                lambda *_,
                v=variable,
                label=value_label:
                label.config(text=str(int(v.get())))
            )

            self.sliders[field_name] = variable

        ttk.Separator(frame).pack(
            fill="x",
            pady=15
        )

        ttk.Label(
            frame,
            text="Черты характера — по одной на строку"
        ).pack(anchor="w")

        self.traits_text = tk.Text(
            frame,
            height=6
        )

        self.traits_text.pack(
            fill="x",
            pady=5
        )

        ttk.Label(
            frame,
            text="Что любит — по одному пункту на строку"
        ).pack(anchor="w")

        self.likes_text = tk.Text(
            frame,
            height=5
        )

        self.likes_text.pack(
            fill="x",
            pady=5
        )

        ttk.Label(
            frame,
            text="Что не любит — по одному пункту на строку"
        ).pack(anchor="w")

        self.dislikes_text = tk.Text(
            frame,
            height=5
        )

        self.dislikes_text.pack(
            fill="x",
            pady=5
        )

    # ---------------------------------------------------------
    # Story
    # ---------------------------------------------------------

    def create_story_tab(self):

        frame = self.story_tab

        ttk.Label(
            frame,
            text="Предыстория персонажа"
        ).pack(anchor="w")

        self.backstory_text = tk.Text(
            frame,
            height=12,
            wrap="word"
        )

        self.backstory_text.pack(
            fill="both",
            expand=True,
            pady=(5, 15)
        )

        ttk.Label(
            frame,
            text="Манера поведения"
        ).pack(anchor="w")

        self.behavior_text = tk.Text(
            frame,
            height=10,
            wrap="word"
        )

        self.behavior_text.pack(
            fill="both",
            expand=True,
            pady=5
        )

        ttk.Label(
            frame,
            text="Правила поведения — по одному правилу на строку"
        ).pack(anchor="w")

        self.rules_text = tk.Text(
            frame,
            height=7,
            wrap="word"
        )

        self.rules_text.pack(
            fill="x",
            pady=5
        )

    # ---------------------------------------------------------
    # Load
    # ---------------------------------------------------------

    def load_character_to_interface(self):

        character = self.character
        personality = character.personality

        self.name_var.set(character.name)
        self.age_var.set(character.age)

        for field_name, variable in self.sliders.items():
            variable.set(
                getattr(
                    personality,
                    field_name
                )
            )

        self.replace_text(
            self.traits_text,
            personality.traits
        )

        self.replace_text(
            self.likes_text,
            personality.likes
        )

        self.replace_text(
            self.dislikes_text,
            personality.dislikes
        )

        self.replace_text(
            self.backstory_text,
            personality.backstory
        )

        self.replace_text(
            self.behavior_text,
            personality.behavior_style
        )

        self.replace_text(
            self.rules_text,
            personality.rules
        )

    @staticmethod
    def replace_text(widget, value):

        widget.delete(
            "1.0",
            tk.END
        )

        if isinstance(value, list):
            value = "\n".join(value)

        widget.insert(
            "1.0",
            value
        )

    # ---------------------------------------------------------
    # Read UI
    # ---------------------------------------------------------

    def read_character_from_interface(self):

        personality = self.character.personality

        self.character.name = self.name_var.get().strip()

        try:
            self.character.age = int(
                self.age_var.get()
            )
        except ValueError:
            self.character.age = 21

        for field_name, variable in self.sliders.items():
            setattr(
                personality,
                field_name,
                float(variable.get())
            )

        personality.traits = self.get_lines(
            self.traits_text
        )

        personality.likes = self.get_lines(
            self.likes_text
        )

        personality.dislikes = self.get_lines(
            self.dislikes_text
        )

        personality.rules = self.get_lines(
            self.rules_text
        )

        personality.backstory = (
            self.backstory_text
            .get("1.0", tk.END)
            .strip()
        )

        personality.behavior_style = (
            self.behavior_text
            .get("1.0", tk.END)
            .strip()
        )

    @staticmethod
    def get_lines(widget):

        return [
            line.strip()
            for line in widget
            .get("1.0", tk.END)
            .splitlines()
            if line.strip()
        ]

    # ---------------------------------------------------------
    # Save
    # ---------------------------------------------------------

    def save_character(self):

        self.read_character_from_interface()

        if not self.character.name:
            messagebox.showwarning(
                "Ошибка",
                "У персонажа должно быть имя."
            )

            return

        self.database.save_character(
            self.character
        )

        messagebox.showinfo(
            "Сохранено",
            (
                "Настройки персонажа сохранены.\n\n"
                f"База:\n{DATABASE_FILE}"
            )
        )

    # ---------------------------------------------------------
    # Reload
    # ---------------------------------------------------------

    def reload_character(self):

        character = self.database.load_character()

        if character is None:
            messagebox.showinfo(
                "Информация",
                "В базе пока нет сохранённого персонажа."
            )

            return

        self.character = character

        self.load_character_to_interface()

        messagebox.showinfo(
            "Загружено",
            "Настройки загружены из базы данных."
        )

    # ---------------------------------------------------------
    # Show
    # ---------------------------------------------------------

    def show_character(self):

        self.read_character_from_interface()

        personality = self.character.personality

        text = (
            f"Имя: {self.character.name}\n"
            f"Возраст: {self.character.age}\n\n"

            f"Дружелюбие: "
            f"{personality.friendliness:.0f}\n"

            f"Любопытство: "
            f"{personality.curiosity:.0f}\n"

            f"Лень: "
            f"{personality.laziness:.0f}\n"

            f"Юмор: "
            f"{personality.humor:.0f}\n"

            f"Хаос: "
            f"{personality.chaos:.0f}\n"

            f"Интеллект: "
            f"{personality.intelligence:.0f}\n"

            f"Смелость: "
            f"{personality.bravery:.0f}\n\n"

            f"Черты:\n"
            f"{', '.join(personality.traits)}\n\n"

            f"Любит:\n"
            f"{', '.join(personality.likes)}\n\n"

            f"Не любит:\n"
            f"{', '.join(personality.dislikes)}\n\n"

            f"Предыстория:\n"
            f"{personality.backstory}\n\n"

            f"Манера поведения:\n"
            f"{personality.behavior_style}\n"
        )

        messagebox.showinfo(
            "Текущий персонаж",
            text
        )

    # ---------------------------------------------------------
    # History
    # ---------------------------------------------------------

    def clear_history(self):

        result = messagebox.askyesno(
            "Очистить историю",
            (
                "Удалить историю взаимодействий "
                "и накопленные воспоминания?"
            )
        )

        if not result:
            return

        with self.database.connect() as connection:

            connection.execute(
                "DELETE FROM interactions"
            )

            connection.execute(
                "DELETE FROM memories"
            )

            connection.commit()

        messagebox.showinfo(
            "Готово",
            "История и память очищены."
        )


def main():

    root = tk.Tk()

    CharacterEditor(root)

    root.mainloop()


if __name__ == "__main__":
    main()