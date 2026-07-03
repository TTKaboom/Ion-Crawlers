# Ion Crawler CLI MVP Blueprint

## Goal

Create a playable command-line prototype that validates the chemistry combat loop before graphics work.

## Implemented Blueprint Modules

- `main.py`: temporary bootstrap entrypoint.
- `game/enums.py`: game modes, difficulty, room types, ion pool type.
- `game/models.py`: domain objects (`Ion`, `Spell`, `Monster`, `Player`, `Room`, `GameState`).
- `game/data.py`: CSV loading/validation and mode-based ion pool splitting.
- `game/combat.py`: encounter state and per-cast combat resolution.
- `game/dungeon.py`: simple grid dungeon generation and movement helpers.
- `game/engine.py`: orchestration for setup, movement, encounters, rewards, run end, scoring.
- `game/cli.py`: CLI session and prompt stubs to fill in next.

## Fixed MVP Defaults

- Single-ion monsters
- One spell per turn
- Damage resolved after each cast
- Overcharge defeats monster and damages player by excess amount
- Difficulty health: Easy 12, Medium 8, Hard 5
- Ion pool: `standard`
- Chest reward: one random spell
- Run ends at exit, player death, or no available spells

## Next Coding Step

Implement `game/cli.py` interactive loop:

1. Start menu (`mode`, `difficulty`, optional `seed`)
2. Main loop commands: `n/s/e/w`, `status`, `spells`, `help`, `quit`
3. Room resolution handlers:
   - Monster encounter prompt and cast flow
   - Chest reward display and claim
   - Exit confirmation and run completion
4. End-of-run summary including score and stats

## Test Coverage Included

- Data parsing and mode filtering
- Combat outcomes (exact, overcharge, wrong sign)
- CLI enum parsing
- Engine setup smoke test

Run tests with:

```bash
python -m unittest discover -q
```
