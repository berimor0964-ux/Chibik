import sys
import threading
import queue
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import tkinter as tk
from tkinter import ttk, messagebox
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
        self.ai_window = None
        self.chat_widget = None
        self.status_label = None
        self.message_entry = None
        self.message_var = None
        self.send_button = None
        self.voice_button = None
        self.message_queue = queue.Queue()
        self.ai_busy = False
        self.closing = False
        self.build_interface()
        self.refresh_characters()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.after(100, self.process_ui_queue)

    def build_interface(self):
        main = ttk.Frame(self.root, padding=20)
        main.pack(fill=tk.BOTH, expand=True)
        ttk.Label(main, text="DESKTOP PET", font=("Segoe UI", 22, "bold")).pack(anchor=tk.W)
        ttk.Label(main, text="Выберите персонажа для запуска", font=("Segoe UI", 11)).pack(anchor=tk.W, pady=(0, 20))
        content = ttk.Frame(main)
        content.pack(fill=tk.BOTH, expand=True)
        left = ttk.LabelFrame(content, text="Персонажи", padding=10)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.character_list = tk.Listbox(left, font=("Segoe UI", 12), activestyle="none")
        self.character_list.pack(fill=tk.BOTH, expand=True)
        self.character_list.bind("<<ListboxSelect>>", self.on_character_select)
        right = ttk.LabelFrame(content, text="Информация", padding=20)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(20, 0))
        self.info_name = ttk.Label(right, text="Персонаж не выбран", font=("Segoe UI", 18, "bold"))
        self.info_name.pack(anchor=tk.W, pady=(0, 10))
        self.info_age = ttk.Label(right, text="")
        self.info_age.pack(anchor=tk.W)
        self.info_traits = ttk.Label(right, text="", wraplength=300, justify=tk.LEFT)
        self.info_traits.pack(anchor=tk.W, pady=(15, 0))
        self.info_backstory = ttk.Label(right, text="", wraplength=300, justify=tk.LEFT)
        self.info_backstory.pack(anchor=tk.W, pady=(15, 0))
        buttons = ttk.Frame(main)
        buttons.pack(fill=tk.X, pady=(20, 0))
        ttk.Button(buttons, text="Создать", command=self.create_character).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(buttons, text="Редактировать", command=self.edit_character).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(buttons, text="Удалить", command=self.delete_character).pack(side=tk.LEFT)
        ttk.Button(buttons, text="▶ Запустить", command=self.start_character).pack(side=tk.RIGHT)

    def refresh_characters(self):
        self.character_list.delete(0, tk.END)
        self.characters = self.database.list_characters()
        for character in self.characters:
            self.character_list.insert(tk.END, f"{character['name']}   |   {character['age']} лет")
        self.selected_character_id = None
        self.clear_info()

    def on_character_select(self, event=None):
        selection = self.character_list.curselection()
        if not selection:
            return
        info = self.characters[selection[0]]
        self.selected_character_id = info["id"]
        character = self.database.load_character_by_id(self.selected_character_id)
        if character is not None:
            self.show_character_info(character)

    def show_character_info(self, character: Character):
        self.info_name.config(text=character.name)
        self.info_age.config(text=f"Возраст: {character.age}")
        p = character.personality
        self.info_traits.config(text="Черты характера:\n" + (", ".join(p.traits) if p.traits else "не заданы"))
        self.info_backstory.config(text="Предыстория:\n" + (p.backstory if p.backstory else "не задана"))

    def clear_info(self):
        self.info_name.config(text="Персонаж не выбран")
        self.info_age.config(text="")
        self.info_traits.config(text="")
        self.info_backstory.config(text="")

    def create_character(self):
        CharacterEditorWindow(self.root, None, self.on_character_saved).show()

    def edit_character(self):
        if not self.selected_character_id:
            messagebox.showwarning("Персонаж", "Сначала выберите персонажа.")
            return
        character = self.database.load_character_by_id(self.selected_character_id)
        if character is None:
            messagebox.showerror("Ошибка", "Не удалось загрузить персонажа.")
            return
        CharacterEditorWindow(self.root, character, self.on_character_saved).show()

    def on_character_saved(self, character: Character):
        self.database.save_character(character)
        self.refresh_characters()
        messagebox.showinfo("Готово", f"Персонаж «{character.name}» сохранён.")

    def delete_character(self):
        if not self.selected_character_id:
            messagebox.showwarning("Персонаж", "Сначала выберите персонажа.")
            return
        character = self.database.load_character_by_id(self.selected_character_id)
        if character is None:
            return
        if not messagebox.askyesno("Удаление", f"Удалить персонажа «{character.name}»?"):
            return
        self.database.delete_character(self.selected_character_id)
        self.refresh_characters()
        messagebox.showinfo("Готово", "Персонаж удалён.")

    def start_character(self):
        if not self.selected_character_id:
            messagebox.showwarning("Запуск", "Сначала выберите персонажа.")
            return
        if self.ai_window is not None:
            try:
                if self.ai_window.winfo_exists():
                    self.ai_window.lift()
                    return
            except tk.TclError:
                pass
        character = self.database.load_character_by_id(self.selected_character_id)
        if character is None:
            messagebox.showerror("Ошибка", "Не удалось загрузить персонажа.")
            return
        self.character = character
        try:
            self.agent = Agent(
                character=self.character,
                llm=LocalLLM(),
                planner=Planner(),
                memory=self.character.memory,
                interaction_saver=self.database.save_interaction,
                memory_saver=self.database.save_memory,
                character_saver=self.database.save_character,
            )
        except Exception as error:
            self.agent = None
            messagebox.showerror("Ошибка AI", str(error), parent=self.root)
            return
        self.open_ai_window()

    def open_ai_window(self):
        window = tk.Toplevel(self.root)
        self.ai_window = window
        window.title(f"Desktop Pet — {self.character.name}")
        window.geometry("700x650")
        window.minsize(520, 450)
        window.protocol("WM_DELETE_WINDOW", self.stop_ai_window)
        ttk.Label(window, text=self.character.name, font=("Segoe UI", 20, "bold")).pack(pady=(15, 5))
        self.status_label = ttk.Label(window, text="AI готов. Напишите сообщение или запустите микрофон.", font=("Segoe UI", 10))
        self.status_label.pack(pady=(0, 10))
        chat_frame = ttk.Frame(window, padding=(10, 0, 10, 10))
        chat_frame.pack(fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(chat_frame, orient=tk.VERTICAL)
        self.chat_widget = tk.Text(chat_frame, state=tk.DISABLED, wrap=tk.WORD, font=("Segoe UI", 11), yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.chat_widget.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Текстовый ввод: Enter или кнопка «Отправить» отправляет сообщение.
        input_frame = ttk.Frame(window, padding=(10, 0, 10, 10))
        input_frame.pack(fill=tk.X)
        self.message_var = tk.StringVar()
        self.message_entry = ttk.Entry(input_frame, textvariable=self.message_var, font=("Segoe UI", 11))
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.message_entry.bind("<Return>", self.send_text_message)
        self.send_button = ttk.Button(input_frame, text="Отправить", command=self.send_text_message)
        self.send_button.pack(side=tk.RIGHT)

        controls = ttk.Frame(window, padding=(10, 0, 10, 10))
        controls.pack(fill=tk.X)
        self.voice_button = ttk.Button(controls, text="🎤 Запустить голос", command=self.start_voice)
        self.voice_button.pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(controls, text="Остановить голос", command=self.stop_voice).pack(side=tk.LEFT)
        ttk.Button(controls, text="Закрыть", command=self.stop_ai_window).pack(side=tk.RIGHT)
        self.add_message(self.character.name, f"Привет! Я {self.character.name}. Можешь написать мне или поговорить через микрофон.")
        self.message_entry.focus_set()

    def add_message(self, speaker: str, message: str):
        try:
            if self.chat_widget is None or not self.chat_widget.winfo_exists():
                return
            self.chat_widget.config(state=tk.NORMAL)
            self.chat_widget.insert(tk.END, f"{speaker}:\n{message}\n\n")
            self.chat_widget.see(tk.END)
            self.chat_widget.config(state=tk.DISABLED)
        except tk.TclError:
            pass

    def send_text_message(self, event=None):
        if self.message_var is None:
            return "break"
        text = self.message_var.get().strip()
        if text:
            self.message_var.set("")
            self.submit_message(text)
        return "break"

    def submit_message(self, text: str):
        if not text.strip() or self.ai_busy or self.agent is None:
            return
        self.ai_busy = True
        self.add_message("Вы", text.strip())
        if self.status_label is not None:
            self.status_label.config(text=f"{self.character.name} думает...")
        if self.send_button is not None:
            self.send_button.config(state=tk.DISABLED)
        if self.message_entry is not None:
            self.message_entry.config(state=tk.DISABLED)
        threading.Thread(target=self._chat_worker, args=(text.strip(),), daemon=True).start()

    def _chat_worker(self, text: str):
        try:
            self.message_queue.put(("response", str(self.agent.chat(text))))
        except Exception as error:
            self.message_queue.put(("error", str(error)))

    def process_ui_queue(self):
        try:
            while True:
                kind, payload = self.message_queue.get_nowait()
                if kind == "voice_input":
                    self.submit_message(payload)
                    continue
                if kind == "response":
                    self.add_message(self.character.name, payload)
                    if self.status_label is not None:
                        self.status_label.config(text="Готов к следующему сообщению.")
                elif kind == "error":
                    self.add_message("Ошибка", payload)
                    if self.status_label is not None:
                        self.status_label.config(text="Ошибка AI.")
                self.ai_busy = False
                if self.send_button is not None:
                    self.send_button.config(state=tk.NORMAL)
                if self.message_entry is not None:
                    self.message_entry.config(state=tk.NORMAL)
                    self.message_entry.focus_set()
        except queue.Empty:
            pass
        except tk.TclError:
            pass
        if not self.closing:
            try:
                self.root.after(100, self.process_ui_queue)
            except tk.TclError:
                pass

    def start_voice(self):
        if self.voice_manager is not None:
            return
        try:
            self.voice_manager = VoiceManager(on_text=self.on_voice_text)
            self.voice_manager.start()
            if self.status_label is not None:
                self.status_label.config(text="🎤 Голосовой ввод активен. Говорите.")
            if self.voice_button is not None:
                self.voice_button.config(text="🎤 Голос активен", state=tk.DISABLED)
        except Exception as error:
            self.voice_manager = None
            messagebox.showerror("Ошибка голоса", str(error), parent=self.ai_window or self.root)

    def on_voice_text(self, text: str):
        # VoiceManager может вызывать callback из другого потока — используем очередь.
        if text and text.strip():
            self.message_queue.put(("voice_input", text.strip()))

    def stop_voice(self):
        if self.voice_manager is not None:
            try:
                self.voice_manager.stop()
            except Exception as error:
                self.message_queue.put(("error", f"Ошибка остановки голоса: {error}"))
            self.voice_manager = None
        if self.status_label is not None:
            self.status_label.config(text="Голосовой ввод остановлен.")
        if self.voice_button is not None:
            self.voice_button.config(text="🎤 Запустить голос", state=tk.NORMAL)

    def stop_ai_window(self):
        self.stop_voice()
        if self.ai_window is not None:
            try:
                self.ai_window.destroy()
            except tk.TclError:
                pass
        self.ai_window = None
        self.chat_widget = self.status_label = self.message_entry = None
        self.message_var = self.send_button = self.voice_button = None
        self.ai_busy = False

    def on_close(self):
        self.closing = True
        if self.voice_manager is not None:
            try:
                self.voice_manager.stop()
            except Exception:
                pass
            self.voice_manager = None
        try:
            self.root.destroy()
        except tk.TclError:
            pass

    def run(self):
        self.root.mainloop()


class CharacterEditorWindow:
    def __init__(self, parent, character: Optional[Character], on_save):
        self.parent = parent
        self.character = character
        self.on_save = on_save
        self.window = tk.Toplevel(parent)
        self.window.title("Создание персонажа" if character is None else f"Редактирование — {character.name}")
        self.window.geometry("700x750")
        self.window.transient(parent)
        self.window.grab_set()
        self.build()

    def build(self):
        main = ttk.Frame(self.window, padding=20)
        main.pack(fill=tk.BOTH, expand=True)
        basic = ttk.LabelFrame(main, text="Основная информация", padding=10)
        basic.pack(fill=tk.X)
        ttk.Label(basic, text="Имя:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.name_var = tk.StringVar(value=self.character.name if self.character else "")
        ttk.Entry(basic, textvariable=self.name_var, width=40).grid(row=0, column=1, sticky=tk.W, padx=10)
        ttk.Label(basic, text="Возраст:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.age_var = tk.IntVar(value=self.character.age if self.character else 20)
        ttk.Spinbox(basic, from_=1, to=150, textvariable=self.age_var, width=10).grid(row=1, column=1, sticky=tk.W, padx=10)
        personality = ttk.LabelFrame(main, text="Личность", padding=10)
        personality.pack(fill=tk.X, pady=15)
        self.traits = {}
        trait_names = [("Дружелюбие", "friendliness"), ("Любопытство", "curiosity"), ("Лень", "laziness"), ("Юмор", "humor"), ("Хаотичность", "chaos"), ("Интеллект", "intelligence"), ("Смелость", "bravery")]
        for row, (label, attribute) in enumerate(trait_names):
            ttk.Label(personality, text=label).grid(row=row, column=0, sticky=tk.W, pady=3)
            value = getattr(self.character.personality, attribute) if self.character else 50
            variable = tk.DoubleVar(value=value)
            self.traits[attribute] = variable
            ttk.Scale(personality, from_=0, to=100, variable=variable, orient=tk.HORIZONTAL, length=250).grid(row=row, column=1, padx=10)
            ttk.Label(personality, textvariable=variable).grid(row=row, column=2)
        ttk.Label(main, text="Предыстория:").pack(anchor=tk.W)
        self.backstory = tk.Text(main, height=5, wrap=tk.WORD)
        self.backstory.pack(fill=tk.X, pady=(5, 15))
        ttk.Label(main, text="Стиль поведения:").pack(anchor=tk.W)
        self.behavior_style = tk.Text(main, height=4, wrap=tk.WORD)
        self.behavior_style.pack(fill=tk.X, pady=(5, 15))
        if self.character:
            self.backstory.insert("1.0", self.character.personality.backstory)
            self.behavior_style.insert("1.0", self.character.personality.behavior_style)
        buttons = ttk.Frame(main)
        buttons.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(buttons, text="Отмена", command=self.window.destroy).pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(buttons, text="Сохранить", command=self.save).pack(side=tk.RIGHT)

    def save(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("Ошибка", "Введите имя персонажа.", parent=self.window)
            return
        try:
            age = int(self.age_var.get())
        except (ValueError, tk.TclError):
            messagebox.showwarning("Ошибка", "Возраст должен быть числом.", parent=self.window)
            return
        if self.character is None:
            character = Character(name=name, age=age)
        else:
            character = self.character
            character.name = name
            character.age = age
        for attribute, variable in self.traits.items():
            setattr(character.personality, attribute, float(variable.get()))
        character.personality.backstory = self.backstory.get("1.0", tk.END).strip()
        character.personality.behavior_style = self.behavior_style.get("1.0", tk.END).strip()
        self.on_save(character)
        self.window.destroy()

    def show(self):
        self.window.wait_window()


if __name__ == "__main__":
    CharacterLauncher().run()
