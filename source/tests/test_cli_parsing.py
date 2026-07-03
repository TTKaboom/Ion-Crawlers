from __future__ import annotations

import unittest

from game.cli import parse_difficulty, parse_mode
from game.enums import Difficulty, GameMode


class TestCliParsing(unittest.TestCase):
    def test_parse_mode_valid_values(self) -> None:
        self.assertIs(parse_mode("anion"), GameMode.ANION)
        self.assertIs(parse_mode("cation"), GameMode.CATION)
        self.assertIs(parse_mode("mixed"), GameMode.MIXED)


    def test_parse_mode_invalid_value(self) -> None:
        with self.assertRaises(ValueError):
            parse_mode("invalid")


    def test_parse_difficulty_valid_values(self) -> None:
        self.assertIs(parse_difficulty("easy"), Difficulty.EASY)
        self.assertIs(parse_difficulty("medium"), Difficulty.MEDIUM)
        self.assertIs(parse_difficulty("hard"), Difficulty.HARD)


if __name__ == "__main__":
    unittest.main()
