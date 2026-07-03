from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .engine import GameEngine, RunConfig
from .enums import Difficulty, GameMode, RoomType, ChargeVisibility
from .dungeon import Dungeon


def render_map(dungeon: Dungeon, player_pos: tuple[int, int]) -> str:
    lines = []
    lines.append("+" + "---+" * dungeon.width)
    for y in range(dungeon.height):
        row_str = "|"
        for x in range(dungeon.width):
            pos = (x, y)
            room = dungeon.room_at(pos)
            if pos == player_pos:
                cell = " P "
            elif not room.visited and pos != dungeon.start_position and pos != dungeon.exit_position:
                cell = " ? "
            else:
                if pos == dungeon.start_position:
                    cell = " S "
                elif pos == dungeon.exit_position:
                    cell = " E "
                elif room.room_type is RoomType.MONSTER and room.monster is not None:
                    cell = " M "
                elif room.room_type is RoomType.CHEST and not room.chest_opened:
                    cell = " C "
                else:
                    cell = "   "
            row_str += cell + "|"
        lines.append(row_str)
        lines.append("+" + "---+" * dungeon.width)
    return "\n".join(lines)


@dataclass
class CliSession:
    engine: GameEngine

    def run(self) -> None:
        state = self.engine.setup()
        player = state.player
        previous_position = player.position

        print("\n" + "=" * 50)
        print("                 ION CRAWLER")
        print("=" * 50)
        print("Your quest: Explore the dungeon, defeat the ion monsters, and find the exit.")
        print(f"You start with {player.health} health and {len(player.spells)} spells.")
        print("=" * 50)

        while player.is_alive():
            current_room = self.engine.dungeon.room_at(player.position)
            current_room.visited = True

            # Resolve current room status first (monster, chest, exit)
            room_status = self.engine.resolve_current_room()
            if room_status == "monster":
                self._handle_encounter(previous_position)
                if not player.is_alive() or self.engine.is_run_over():
                    break
                continue
            elif room_status == "chest":
                self._handle_chest()
                continue
            elif room_status == "exit":
                if self._handle_exit():
                    break

            if self.engine.is_run_over():
                break

            # Print current state & Map
            print("\n" + "=" * 40)
            print(f"Position: {player.position} | Health: {player.health}/{self.engine.config.difficulty.starting_health} | Spells: {len(player.available_spells())}")
            print("=" * 40)
            print(render_map(self.engine.dungeon, player.position))

            # Get next command
            try:
                cmd = input("\nEnter command (n/s/e/w to move, status, spells, help, quit): ").strip().lower()
            except (KeyboardInterrupt, EOFError):
                print("\nQuitting game...")
                return

            if not cmd:
                continue

            if cmd in {"n", "s", "e", "w", "north", "south", "east", "west"}:
                dir_char = cmd[0]
                old_pos = player.position
                if self.engine.move_player(dir_char):
                    previous_position = old_pos
                    print(f"Moved {cmd.upper()}.")
                else:
                    print("You can't go that way! Out of bounds.")
            elif cmd in {"status", "stat", "state"}:
                self._print_status()
            elif cmd in {"spells", "spell", "i", "inv", "inventory"}:
                self._print_spells()
            elif cmd in {"help", "h", "?"}:
                self._print_help()
            elif cmd in {"quit", "q", "exit"}:
                try:
                    confirm = input("Are you sure you want to quit? (y/n): ").strip().lower()
                except (KeyboardInterrupt, EOFError):
                    return
                if confirm.startswith("y"):
                    print("Quitting game. Thanks for playing!")
                    return
            else:
                print("Unknown command. Type 'help' for options.")

        # Show game summary
        self.show_game_summary()

    def _handle_encounter(self, previous_position: tuple[int, int]) -> None:
        player = self.engine.state.player
        try:
            encounter = self.engine.start_encounter()
        except ValueError:
            print("Error: No monster in current room.")
            return

        monster = encounter.monster
        show_monster = self.engine.config.visibility in {ChargeVisibility.BOTH, ChargeVisibility.MONSTERS_ONLY}
        show_spells = self.engine.config.visibility in {ChargeVisibility.BOTH, ChargeVisibility.SPELLS_ONLY}

        print("\n" + "!" * 50)
        print("                 MONSTER ENCOUNTER!")
        print("!" * 50)
        print(f"You encounter: {monster.name.upper()} ({monster.ions[0].formula})")
        if show_monster:
            print(f"Monster Charge: {monster.net_charge:+d}")
        else:
            print("Monster Charge: [HIDDEN]")
        print("!" * 50)

        while not encounter.is_complete and player.is_alive():
            available = player.available_spells()
            if not available:
                print("\nYou are out of spells! You cannot fight.")
                break

            if show_monster:
                print(f"\nMonster remaining charge: {encounter.remaining_charge:+d}")
            else:
                print("\nMonster remaining charge: [HIDDEN]")

            print("Your Spells:")
            for idx, spell in enumerate(player.spells):
                if not spell.used:
                    if show_spells:
                        sign_str = "+" if spell.charge > 0 else ""
                        print(f"  [{idx + 1}] {spell.ion.name} ({spell.ion.formula}) [Charge: {sign_str}{spell.charge}]")
                    else:
                        print(f"  [{idx + 1}] {spell.ion.name} ({spell.ion.formula}) [Charge: HIDDEN]")

            try:
                choice = input("\nSelect a spell to cast (number) or type 'retreat' to flee: ").strip().lower()
            except (KeyboardInterrupt, EOFError):
                print("\nQuitting encounter...")
                return

            if choice in {"retreat", "r", "flee"}:
                player.position = previous_position
                print(f"\nYou fled back to {previous_position}!")
                return

            try:
                spell_idx = int(choice) - 1
                if spell_idx < 0 or spell_idx >= len(player.spells) or player.spells[spell_idx].used:
                    print("Invalid choice. Please select an available spell number.")
                    continue
            except ValueError:
                print("Invalid input. Please enter a spell number or 'retreat'.")
                continue

            # Cast the spell
            if show_spells:
                print(f"\nYou cast {player.spells[spell_idx].ion.name} ({player.spells[spell_idx].ion.formula}, charge {player.spells[spell_idx].charge:+d})!")
            else:
                print(f"\nYou cast {player.spells[spell_idx].ion.name} ({player.spells[spell_idx].ion.formula}, charge HIDDEN)!")

            result = self.engine.cast_spell(encounter, spell_idx)

            print(result.message)
            if result.damage > 0:
                print(f"💥 Ouch! You took {result.damage} damage!")
                print(f"Your remaining health: {player.health}/{self.engine.config.difficulty.starting_health}")

            if result.defeated:
                room = self.engine.dungeon.room_at(player.position)
                room.monster = None
                room.monster_defeated = True
                print(f"✨ Victory! You defeated the {monster.name.upper()}!")
                break

        # Show final revealed details (charges/answers recap) if any charges were hidden
        if not show_monster or not show_spells:
            print("\n" + "=" * 50)
            print("                 REVEALED BATTLE DETAILS")
            print("=" * 50)
            print(f"Monster: {monster.name.upper()} ({monster.ions[0].formula})")
            print(f"  -> Actual Net Charge: {monster.net_charge:+d}")
            if len(monster.ions) > 1:
                print("  -> Composed of:")
                for ion in monster.ions:
                    print(f"     - {ion.name} ({ion.formula}): {ion.charge:+d}")

            print("\nYour Spells & Charges:")
            for idx, spell in enumerate(player.spells):
                used_status = "[USED]" if spell.used else "[UNUSED]"
                sign_str = "+" if spell.charge > 0 else ""
                print(f"  - {spell.ion.name} ({spell.ion.formula}): {sign_str}{spell.charge} {used_status}")
            print("=" * 50)

    def _handle_chest(self) -> None:
        room = self.engine.dungeon.room_at(self.engine.state.player.position)
        spell = self.engine.grant_chest_reward()
        room.chest_opened = True

        print("\n" + "*" * 50)
        print("                 TREASURE CHEST!")
        print("*" * 50)
        print("You found a hidden treasure chest!")
        print(f"Inside, you discover a new spell:")
        sign_str = "+" if spell.charge > 0 else ""
        print(f"  -> {spell.ion.name} ({spell.ion.formula}) [Charge: {sign_str}{spell.charge}]")
        print("It has been added to your spellbook!")
        print("*" * 50)

    def _handle_exit(self) -> bool:
        print("\n" + "H" * 50)
        print("                 THE DUNGEON EXIT")
        print("H" * 50)
        print("You see the heavy iron door leading out of the dungeon.")
        try:
            choice = input("Do you want to escape and complete your run? (y/n): ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            return True
        if choice.startswith("y"):
            return True
        return False

    def _print_status(self) -> None:
        player = self.engine.state.player
        print("\n--- PLAYER STATUS ---")
        print(f"Health:            {player.health}/{self.engine.config.difficulty.starting_health}")
        print(f"Monsters Defeated: {player.monsters_defeated}")
        print(f"Damage Taken:      {player.total_damage_taken}")
        print(f"Available Spells:  {len(player.available_spells())}")
        print(f"Current Position:  {player.position}")
        print(f"Dungeon Exit:      {self.engine.dungeon.exit_position}")

    def _print_spells(self) -> None:
        player = self.engine.state.player
        show_spells = self.engine.config.visibility in {ChargeVisibility.BOTH, ChargeVisibility.SPELLS_ONLY}
        print("\n--- SPELLBOOK ---")
        available = [s for s in player.spells if not s.used]
        used = [s for s in player.spells if s.used]

        print("Available Spells:")
        if not available:
            print("  (None)")
        for idx, spell in enumerate(player.spells):
            if not spell.used:
                if show_spells:
                    sign_str = "+" if spell.charge > 0 else ""
                    print(f"  [{idx + 1}] {spell.ion.name} ({spell.ion.formula}) [Charge: {sign_str}{spell.charge}]")
                else:
                    print(f"  [{idx + 1}] {spell.ion.name} ({spell.ion.formula}) [Charge: HIDDEN]")

        print("\nUsed Spells:")
        if not used:
            print("  (None)")
        for spell in used:
            if show_spells:
                sign_str = "+" if spell.charge > 0 else ""
                print(f"  [x] {spell.ion.name} ({spell.ion.formula}) [Charge: {sign_str}{spell.charge}]")
            else:
                print(f"  [x] {spell.ion.name} ({spell.ion.formula}) [Charge: HIDDEN]")

    def _print_help(self) -> None:
        print("\n--- HOW TO PLAY ---")
        print("Navigate the dungeon, neutralize monster charges, and escape!")
        print("\nCommands:")
        print("  n / s / e / w  : Move North, South, East, or West")
        print("  status         : View current health, position, and stats")
        print("  spells         : View your spellbook (available and used spells)")
        print("  help           : Display this help message")
        print("  quit           : Exit the game immediately")
        print("\nCombat Rules:")
        print("  - To defeat a monster, cast opposite-sign spells to reduce its charge to 0.")
        print("  - If you overcharge the monster (exceed opposite charge), it is defeated")
        print("    but you take the excess charge as damage!")
        print("  - Casting a same-sign spell damages you by its charge magnitude!")

    def show_game_summary(self) -> None:
        player = self.engine.state.player
        score = self.engine.finalize_score()

        print("\n" + "=" * 50)
        if not player.is_alive():
            print("                 💀 GAME OVER 💀")
            print("         You succumbed to your injuries.")
        elif player.position == self.engine.dungeon.exit_position:
            print("                 🎉 VICTORY! 🎉")
            print("       You successfully escaped the dungeon!")
        else:
            print("                 💀 GAME OVER 💀")
            print("       You ran out of spells to defeat monsters.")
        print("=" * 50)

        print(f"Difficulty:        {self.engine.config.difficulty.name.upper()}")
        print(f"Mode:              {self.engine.config.mode.name.upper()}")
        print(f"Monsters Defeated: {player.monsters_defeated}")
        print(f"Damage Taken:      {player.total_damage_taken}")
        print(f"Total Offset:      {player.total_charge_offset} / {self.engine.state.total_required_charge}")
        print(f"Final Score:       {score:.1f}%")
        print("=" * 50)


def build_config_from_prompts() -> RunConfig:
    print("\n" + "=" * 50)
    print("                 ION CRAWLER")
    print("=================================================")
    print("Welcome to Ion Crawler! Please configure your game.")
    print("=================================================\n")

    # Mode selection
    while True:
        print("Select Game Mode:")
        print("  1. Anion (Monsters are anions, player casts cation spells)")
        print("  2. Cation (Monsters are cations, player casts anion spells)")
        print("  3. Mixed (Monsters are both, player casts both)")
        choice = input("Enter choice (1-3 or name): ").strip().lower()
        if choice in {"1", "anion"}:
            mode = GameMode.ANION
            break
        elif choice in {"2", "cation"}:
            mode = GameMode.CATION
            break
        elif choice in {"3", "mixed"}:
            mode = GameMode.MIXED
            break
        else:
            print("Invalid selection. Please choose 1, 2, or 3.")

    print()
    # Difficulty selection
    while True:
        print("Select Difficulty:")
        print("  1. Easy (12 Starting Health)")
        print("  2. Medium (8 Starting Health)")
        print("  3. Hard (5 Starting Health)")
        choice = input("Enter choice (1-3 or name): ").strip().lower()
        if choice in {"1", "easy"}:
            difficulty = Difficulty.EASY
            break
        elif choice in {"2", "medium"}:
            difficulty = Difficulty.MEDIUM
            break
        elif choice in {"3", "hard"}:
            difficulty = Difficulty.HARD
            break
        else:
            print("Invalid selection. Please choose 1, 2, or 3.")

    print()
    # Visibility selection
    while True:
        print("Select Charge Visibility Mode:")
        print("  1. Both (Show both spell and monster charges)")
        print("  2. Spells Only (Show spell charges, hide monster charges)")
        print("  3. Monsters Only (Show monster charges, hide spell charges)")
        print("  4. Neither (Hide both spell and monster charges)")
        choice = input("Enter choice (1-4 or name): ").strip().lower()
        if choice in {"1", "both"}:
            visibility = ChargeVisibility.BOTH
            break
        elif choice in {"2", "spells only", "spells_only", "spells"}:
            visibility = ChargeVisibility.SPELLS_ONLY
            break
        elif choice in {"3", "monsters only", "monsters_only", "monsters"}:
            visibility = ChargeVisibility.MONSTERS_ONLY
            break
        elif choice in {"4", "neither"}:
            visibility = ChargeVisibility.NEITHER
            break
        else:
            print("Invalid selection. Please choose 1, 2, 3, or 4.")

    print()
    # Optional seed selection
    seed = None
    while True:
        choice = input("Enter seed (integer, press Enter for random): ").strip()
        if not choice:
            break
        try:
            seed = int(choice)
            break
        except ValueError:
            print("Invalid input. Seed must be an integer.")

    return RunConfig(
        mode=mode,
        difficulty=difficulty,
        visibility=visibility,
        csv_path=Path("ions.csv"),
        rng_seed=seed,
    )


def parse_mode(value: str) -> GameMode:
    text = value.strip().lower()
    if text == "anion":
        return GameMode.ANION
    if text == "cation":
        return GameMode.CATION
    if text == "mixed":
        return GameMode.MIXED
    raise ValueError(f"Unsupported mode: {value}")


def parse_difficulty(value: str) -> Difficulty:
    text = value.strip().lower()
    if text == "easy":
        return Difficulty.EASY
    if text == "medium":
        return Difficulty.MEDIUM
    if text == "hard":
        return Difficulty.HARD
    raise ValueError(f"Unsupported difficulty: {value}")
