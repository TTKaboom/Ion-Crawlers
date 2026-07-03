from __future__ import annotations

from pathlib import Path
import unittest

from game.engine import GameEngine, RunConfig
from game.enums import Difficulty, GameMode


class TestEngineSetup(unittest.TestCase):
    def test_engine_setup_builds_state_and_dungeon(self) -> None:
        config = RunConfig(
            mode=GameMode.ANION,
            difficulty=Difficulty.EASY,
            csv_path=Path("ions.csv"),
            rng_seed=1,
        )
        engine = GameEngine(config)

        state = engine.setup()

        self.assertEqual(state.player.health, 12)
        self.assertIsNotNone(engine.dungeon)
        self.assertGreater(state.total_required_charge, 0)
        self.assertEqual(len(state.player.spells), config.starting_spell_count)


if __name__ == "__main__":
    unittest.main()
