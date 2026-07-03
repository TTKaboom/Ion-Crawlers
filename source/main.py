from __future__ import annotations

from pathlib import Path

from game.cli import CliSession
from game.engine import GameEngine, RunConfig
from game.enums import Difficulty, GameMode


def main() -> None:
    """Main game entrypoint."""
    from game.cli import build_config_from_prompts
    try:
        config = build_config_from_prompts()
    except (KeyboardInterrupt, EOFError):
        print("\nGoodbye!")
        return

    engine = GameEngine(config)
    engine.setup()

    session = CliSession(engine)
    try:
        session.run()
    except (KeyboardInterrupt, EOFError):
        print("\nGame interrupted. Goodbye!")


if __name__ == "__main__":
    main()
