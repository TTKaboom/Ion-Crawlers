from __future__ import annotations

from enum import Enum


class GameMode(str, Enum):
    ANION = "anion"
    CATION = "cation"
    MIXED = "mixed"


class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

    @property
    def starting_health(self) -> int:
        if self is Difficulty.EASY:
            return 12
        if self is Difficulty.MEDIUM:
            return 8
        return 5


class ChargeVisibility(str, Enum):
    BOTH = "both"
    SPELLS_ONLY = "spells_only"
    MONSTERS_ONLY = "monsters_only"
    NEITHER = "neither"


class RoomType(str, Enum):
    START = "start"
    EMPTY = "empty"
    MONSTER = "monster"
    CHEST = "chest"
    EXIT = "exit"


class IonPoolType(str, Enum):
    STANDARD = "standard"
    EXTENDED = "extended"
    ALL = "all"
