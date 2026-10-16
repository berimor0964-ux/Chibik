from dataclasses import dataclass


@dataclass
class Needs:

    hunger: float = 50.0
    energy: float = 100.0
    fun: float = 50.0
    social: float = 50.0
    hygiene: float = 50.0
    comfort: float = 50.0

    @staticmethod
    def _clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
        return max(minimum, min(value, maximum))

    def change_hunger(self, amount: float) -> None:
        self.hunger = self._clamp(self.hunger + amount)

    def change_energy(self, amount: float) -> None:
        self.energy = self._clamp(self.energy + amount)

    def change_fun(self, amount: float) -> None:
        self.fun = self._clamp(self.fun + amount)

    def change_social(self, amount: float) -> None:
        self.social = self._clamp(self.social + amount)

    def change_hygiene(self, amount: float) -> None:
        self.hygiene = self._clamp(self.hygiene + amount)

    def change_comfort(self, amount: float) -> None:
        self.comfort = self._clamp(self.comfort + amount)