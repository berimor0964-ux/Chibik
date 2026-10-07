from dataclasses import dataclass, field


@dataclass
class Personality:
    friendliness: float = 50.0
    curiosity: float = 50.0
    laziness: float = 50.0
    humor: float = 50.0
    chaos: float = 50.0
    intelligence: float = 50.0
    bravery: float = 50.0

    traits: list[str] = field(
        default_factory=list
    )

    backstory: str = ""

    behavior_style: str = ""

    likes: list[str] = field(
        default_factory=list
    )

    dislikes: list[str] = field(
        default_factory=list
    )

    rules: list[str] = field(
        default_factory=list
    )

    # =========================================================
    # BASIC METHODS
    # =========================================================

    def add_trait(
        self,
        trait: str
    ) -> None:

        if trait not in self.traits:
            self.traits.append(trait)

    def remove_trait(
        self,
        trait: str
    ) -> None:

        if trait in self.traits:
            self.traits.remove(trait)

    def add_like(
        self,
        item: str
    ) -> None:

        if item not in self.likes:
            self.likes.append(item)

    def add_dislike(
        self,
        item: str
    ) -> None:

        if item not in self.dislikes:
            self.dislikes.append(item)

    def add_rule(
        self,
        rule: str
    ) -> None:

        if rule not in self.rules:
            self.rules.append(rule)

    # =========================================================
    # DESCRIPTION
    # =========================================================

    def build_description(self) -> str:

        parts = []

        if self.backstory:
            parts.append(
                f"Предыстория: {self.backstory}"
            )

        if self.behavior_style:
            parts.append(
                f"Манера поведения: "
                f"{self.behavior_style}"
            )

        if self.traits:
            parts.append(
                "Черты характера: "
                + ", ".join(self.traits)
            )

        if self.likes:
            parts.append(
                "Любит: "
                + ", ".join(self.likes)
            )

        if self.dislikes:
            parts.append(
                "Не любит: "
                + ", ".join(self.dislikes)
            )

        if self.rules:
            parts.append(
                "Правила поведения: "
                + "; ".join(self.rules)
            )

        return "\n".join(parts)

    # =========================================================
    # CLAMP
    # =========================================================

    @staticmethod
    def clamp(
        value: float
    ) -> float:

        return max(
            0.0,
            min(
                100.0,
                value
            )
        )

    # =========================================================
    # DEVELOPMENT
    # =========================================================

    def change_trait_value(
        self,
        trait_name: str,
        amount: float
    ) -> bool:

        if not hasattr(
            self,
            trait_name
        ):
            return False

        current = getattr(
            self,
            trait_name
        )

        new_value = self.clamp(
            current + amount
        )

        setattr(
            self,
            trait_name,
            new_value
        )

        return True

    def develop_from_message(
        self,
        message: str
    ) -> list[str]:
        """
        Анализирует поведение пользователя
        и постепенно изменяет характер персонажа.

        Возвращает список изменений.
        """

        text = message.lower()

        changes = []

        # -----------------------------------------------------
        # HUMOR
        # -----------------------------------------------------

        humor_words = [
            "шутка",
            "шутку",
            "смешно",
            "смешная",
            "смешной",
            "ахах",
            "хаха",
            "лол",
            "прикол",
            "мем"
        ]

        if any(
            word in text
            for word in humor_words
        ):

            old = self.humor

            self.change_trait_value(
                "humor",
                0.5
            )

            if self.humor != old:
                changes.append(
                    "юмор +0.5"
                )

        # -----------------------------------------------------
        # CURIOSITY
        # -----------------------------------------------------

        curiosity_words = [
            "почему",
            "зачем",
            "как работает",
            "интересно",
            "расскажи",
            "объясни",
            "исследовать",
            "узнать",
            "что будет"
        ]

        if any(
            word in text
            for word in curiosity_words
        ):

            old = self.curiosity

            self.change_trait_value(
                "curiosity",
                0.5
            )

            if self.curiosity != old:
                changes.append(
                    "любопытство +0.5"
                )

        # -----------------------------------------------------
        # FRIENDLINESS
        # -----------------------------------------------------

        friendly_words = [
            "спасибо",
            "молодец",
            "класс",
            "отлично",
            "люблю",
            "нравишься",
            "хорошая",
            "умница"
        ]

        if any(
            word in text
            for word in friendly_words
        ):

            old = self.friendliness

            self.change_trait_value(
                "friendliness",
                0.5
            )

            if self.friendliness != old:
                changes.append(
                    "дружелюбие +0.5"
                )

        # -----------------------------------------------------
        # BRAVERY
        # -----------------------------------------------------

        brave_words = [
            "риск",
            "рискнуть",
            "опасно",
            "смело",
            "попробуй",
            "не бойся",
            "эксперимент"
        ]

        if any(
            word in text
            for word in brave_words
        ):

            old = self.bravery

            self.change_trait_value(
                "bravery",
                0.5
            )

            if self.bravery != old:
                changes.append(
                    "смелость +0.5"
                )

        # -----------------------------------------------------
        # CHAOS
        # -----------------------------------------------------

        chaos_words = [
            "сломай",
            "хаос",
            "безумие",
            "эксперимент",
            "сделай наоборот",
            "что-нибудь странное"
        ]

        if any(
            word in text
            for word in chaos_words
        ):

            old = self.chaos

            self.change_trait_value(
                "chaos",
                0.5
            )

            if self.chaos != old:
                changes.append(
                    "хаотичность +0.5"
                )

        # -----------------------------------------------------
        # LAZINESS
        # -----------------------------------------------------

        lazy_words = [
            "не хочу делать",
            "лень",
            "давай проще",
            "сделай за меня",
            "не буду делать"
        ]

        if any(
            word in text
            for word in lazy_words
        ):

            old = self.laziness

            self.change_trait_value(
                "laziness",
                0.5
            )

            if self.laziness != old:
                changes.append(
                    "лень +0.5"
                )

        # -----------------------------------------------------
        # INTELLIGENCE / COMPLEXITY
        # -----------------------------------------------------

        complex_words = [
            "алгоритм",
            "архитектура",
            "математика",
            "программирование",
            "python",
            "sql",
            "нейросеть",
            "машинное обучение",
            "искусственный интеллект"
        ]

        if any(
            word in text
            for word in complex_words
        ):

            old = self.intelligence

            self.change_trait_value(
                "intelligence",
                0.25
            )

            if self.intelligence != old:
                changes.append(
                    "интеллект +0.25"
                )

        return changes