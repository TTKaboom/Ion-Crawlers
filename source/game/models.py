from __future__ import annotations

from dataclasses import dataclass, field

from .enums import Difficulty, GameMode, RoomType


@dataclass(frozen=True)
class Ion:
    name: str
    formula: str
    charge: int
    ion_type: str

    @property
    def is_cation(self) -> bool:
        return self.charge > 0

    @property
    def is_anion(self) -> bool:
        return self.charge < 0


@dataclass
class Spell:
    ion: Ion
    used: bool = False

    @property
    def charge(self) -> int:
        return self.ion.charge


@dataclass
class Monster:
    ions: list[Ion]
    name: str

    @property
    def net_charge(self) -> int:
        return sum(ion.charge for ion in self.ions)


@dataclass
class Player:
    health: int
    spells: list[Spell] = field(default_factory=list)
    position: tuple[int, int] = (0, 0)

    total_damage_taken: int = 0
    total_charge_offset: int = 0
    monsters_defeated: int = 0

    @classmethod
    def from_difficulty(cls, difficulty: Difficulty) -> "Player":
        return cls(health=difficulty.starting_health)

    def is_alive(self) -> bool:
        return self.health > 0

    def take_damage(self, amount: int) -> None:
        if amount <= 0:
            return
        self.health -= amount
        self.total_damage_taken += amount

    def add_spell(self, spell: Spell) -> None:
        self.spells.append(spell)

    def available_spells(self) -> list[Spell]:
        return [spell for spell in self.spells if not spell.used]

    def mark_spell_used(self, spell_index: int) -> Spell:
        spell = self.spells[spell_index]
        spell.used = True
        return spell


@dataclass
class Room:
    room_type: RoomType
    position: tuple[int, int]
    monster: Monster | None = None
    chest_opened: bool = False
    visited: bool = False


@dataclass
class GameState:
    mode: GameMode
    difficulty: Difficulty
    player: Player
    score_percent: float = 0.0
    total_required_charge: int = 0
