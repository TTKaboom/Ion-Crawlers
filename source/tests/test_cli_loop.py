from __future__ import annotations

import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

from game.engine import GameEngine, RunConfig
from game.enums import Difficulty, GameMode, ChargeVisibility
from game.cli import CliSession, build_config_from_prompts


class TestCliLoop(unittest.TestCase):
    @patch("builtins.input")
    @patch("builtins.print")
    def test_build_config_from_prompts(self, mock_print: MagicMock, mock_input: MagicMock) -> None:
        # Simulate selecting Mixed, Easy, Both visibility, and empty seed
        mock_input.side_effect = ["3", "1", "1", ""]
        config = build_config_from_prompts()

        self.assertEqual(config.mode, GameMode.MIXED)
        self.assertEqual(config.difficulty, Difficulty.EASY)
        self.assertEqual(config.visibility, ChargeVisibility.BOTH)
        self.assertIsNone(config.rng_seed)

    @patch("builtins.input")
    @patch("builtins.print")
    def test_cli_session_quit_immediately(self, mock_print: MagicMock, mock_input: MagicMock) -> None:
        config = RunConfig(
            mode=GameMode.ANION,
            difficulty=Difficulty.EASY,
            csv_path=Path("ions.csv"),
            rng_seed=42,
        )
        engine = GameEngine(config)

        # Simulate typing 'quit', then 'y' to confirm
        mock_input.side_effect = ["quit", "y"]
        session = CliSession(engine)
        session.run()

        # Check that setup was called and game ran without crashing
        self.assertIsNotNone(engine.state)
        self.assertTrue(any("Quitting game" in call[0][0] for call in mock_print.call_args_list if call[0]))

    @patch("builtins.input")
    @patch("builtins.print")
    def test_cli_session_movement(self, mock_print: MagicMock, mock_input: MagicMock) -> None:
        config = RunConfig(
            mode=GameMode.ANION,
            difficulty=Difficulty.EASY,
            csv_path=Path("ions.csv"),
            rng_seed=42,
        )
        engine = GameEngine(config)

        # Move east, status, help, quit
        mock_input.side_effect = ["e", "status", "help", "quit", "y"]
        session = CliSession(engine)
        session.run()

        self.assertEqual(engine.state.player.position, (1, 0))
        self.assertTrue(any("Moved E." in call[0][0] for call in mock_print.call_args_list if call[0]))

    @patch("builtins.input")
    @patch("builtins.print")
    def test_cli_session_hide_charges_and_reveal(self, mock_print: MagicMock, mock_input: MagicMock) -> None:
        config = RunConfig(
            mode=GameMode.ANION,
            difficulty=Difficulty.EASY,
            visibility=ChargeVisibility.NEITHER,  # Hide both
            csv_path=Path("ions.csv"),
            rng_seed=42,
        )
        engine = GameEngine(config)

        # Move to a room, trigger encounter, cast first spell (1), fail or win, then quit
        # Wait! Let's check which room has a monster. With rng_seed=42, let's look at the layout.
        # But we can also manually place a monster in (0, 0) and trigger encounter!
        session = CliSession(engine)
        state = engine.setup()
        
        # Place monster in (0, 0) and set player position to (0, 0)
        from game.enums import RoomType
        from game.models import Monster, Ion
        room = engine.dungeon.room_at((0, 0))
        room.room_type = RoomType.MONSTER
        room.monster = Monster(ions=[Ion("bromide", "Br", -1, "standard")], name="bromide")
        
        # Player casts first spell (index 1 is 1-based, input choice "1" then quit)
        mock_input.side_effect = ["1", "quit", "y"]
        session._handle_encounter(previous_position=(0, 0))

        # Check that HIDDEN was printed during combat
        printed_texts = [call[0][0] for call in mock_print.call_args_list if call[0]]
        self.assertTrue(any("HIDDEN" in text for text in printed_texts))
        
        # Check that final reveal section printed actual charges
        self.assertTrue(any("REVEALED BATTLE DETAILS" in text for text in printed_texts))
        self.assertTrue(any("Actual Net Charge:" in text for text in printed_texts))


if __name__ == "__main__":
    unittest.main()
