from dataclasses import dataclass, field


@dataclass
class Relationship:
    character_id: str
    friendship: float = 50.0
    trust: float = 50.0
    respect: float = 50.0
    affection: float = 50.0

    def _clamp(
        self,
        value: float,
        minimum: float = 0.0,
        maximum: float = 100.0
    ) -> float:
        return max(minimum, min(value, maximum))

    def change_friendship(self, amount: float) -> None:
        self.friendship = self._clamp(
            self.friendship + amount
        )

    def change_trust(self, amount: float) -> None:
        self.trust = self._clamp(
            self.trust + amount
        )

    def change_respect(self, amount: float) -> None:
        self.respect = self._clamp(
            self.respect + amount
        )

    def change_affection(self, amount: float) -> None:
        self.affection = self._clamp(
            self.affection + amount
        )


@dataclass
class Relationships:
    relations: dict[str, Relationship] = field(
        default_factory=dict
    )

    def get(self, character_id: str) -> Relationship | None:
        return self.relations.get(character_id)

    def add(self, character_id: str) -> Relationship:
        relationship = Relationship(
            character_id=character_id
        )

        self.relations[character_id] = relationship

        return relationship

    def remove(self, character_id: str) -> None:
        self.relations.pop(character_id, None)

    def get_or_create(
        self,
        character_id: str
    ) -> Relationship:
        relationship = self.get(character_id)

        if relationship is None:
            relationship = self.add(character_id)

        return relationship