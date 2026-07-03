from __future__ import annotations

import unittest
from pathlib import Path

from game.engine import GameEngine, RunConfig
from game.enums import Difficulty, GameMode
from game.models import Spell, Ion


class TestDefeatableMonster(unittest.TestCase):
    def test_monster_charge_limited_to_defeatable_subset_sums(self) -> None:
        config = RunConfig(
            mode=GameMode.ANION,
            difficulty=Difficulty.EASY,
            csv_path=Path("ions.csv"),
            rng_seed=42,
        )
        engine = GameEngine(config)
        engine.setup()

        # Manually set player's spells to only have +2 and +4 charges
        player = engine.state.player
        player.spells = [
            Spell(Ion("calcium", "Ca", 2, "standard")),
            Spell(Ion("lead(IV)", "Pb", 4, "extended")),
        ]

        # Call start_encounter to trigger dynamic monster generation for current room
        room = engine.dungeon.room_at(player.position)
        # Ensure the room is a monster room for testing
        from game.enums import RoomType
        room.room_type = RoomType.MONSTER

        # Start encounter
        encounter = engine.start_encounter()
        monster = encounter.monster

        # The monster net charge must be in {-2, -4, -6}
        self.assertIn(monster.net_charge, {-2, -4, -6})
        self.assertNotIn(monster.net_charge, {-1, -3, -5})

    def test_cation_mode_defeatable_monster(self) -> None:
        config = RunConfig(
            mode=GameMode.CATION,
            difficulty=Difficulty.EASY,
            csv_path=Path("ions.csv"),
            rng_seed=42,
        )
        engine = GameEngine(config)
        engine.setup()

        # Manually set player's spells to only have -2 and -3 charges
        player = engine.state.player
        player.spells = [
            Spell(Ion("carbonate", "CO3", -2, "standard")),
            Spell(Ion("nitride", "N", -3, "standard")),
        ]

        room = engine.dungeon.room_at(player.position)
        from game.enums import RoomType
        room.room_type = RoomType.MONSTER

        encounter = engine.start_encounter()
        monster = encounter.monster

        # The monster net charge must be in {2, 3, 5}
        self.assertIn(monster.net_charge, {2, 3, 5})
        self.assertNotIn(monster.net_charge, {1, 4, 6})


if __name__ == "__main__":
    unittest.main()
