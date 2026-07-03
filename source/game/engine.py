from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path

from .combat import EncounterResolver, EncounterState
from .data import CsvIonRepository
from .dungeon import Dungeon, DungeonFactory
from .enums import Difficulty, GameMode, IonPoolType, RoomType, ChargeVisibility
from .models import GameState, Player, Spell, Monster, Ion


def get_possible_subset_sums(charges: list[int]) -> set[int]:
    sums = {0}
    for c in charges:
        new_sums = set()
        for s in sums:
            new_sums.add(s + c)
        sums.update(new_sums)
    if 0 in sums:
        sums.remove(0)
    return sums


@dataclass
class RunConfig:
    mode: GameMode
    difficulty: Difficulty
    csv_path: Path
    pool_type: IonPoolType = IonPoolType.STANDARD
    visibility: ChargeVisibility = ChargeVisibility.BOTH
    starting_spell_count: int = 6
    dungeon_width: int = 4
    dungeon_height: int = 4
    monster_room_count: int = 6
    chest_room_count: int = 3
    rng_seed: int | None = None


class GameEngine:
    def __init__(self, config: RunConfig) -> None:
        self.config = config
        self.rng = random.Random(config.rng_seed)
        self.data = CsvIonRepository(config.csv_path, config.pool_type)
        self.resolver = EncounterResolver()
        self.state: GameState | None = None
        self.dungeon: Dungeon | None = None
        self.monster_pool: list[Ion] = []
        self.spell_pool: list[Ion] = []

    def setup(self) -> GameState:
        ions = self.data.load_ions()
        self.monster_pool, self.spell_pool = self.data.for_mode(self.config.mode, ions)

        player = Player.from_difficulty(self.config.difficulty)
        for _ in range(self.config.starting_spell_count):
            ion = self.rng.choice(self.spell_pool)
            player.add_spell(Spell(ion=ion))

        dungeon = DungeonFactory(self.rng).build_simple_dungeon(
            width=self.config.dungeon_width,
            height=self.config.dungeon_height,
            monster_pool=self.monster_pool,
            monster_room_count=self.config.monster_room_count,
            chest_room_count=self.config.chest_room_count,
        )
        player.position = dungeon.start_position

        self.dungeon = dungeon
        self.state = GameState(mode=self.config.mode, difficulty=self.config.difficulty, player=player)
        self._compute_total_required_charge()
        return self.state

    def run_cli(self) -> None:
        """Blueprint CLI loop entrypoint for MVP."""
        raise NotImplementedError("CLI loop implementation comes in the next step")

    def move_player(self, direction: str) -> bool:
        if not self.state or not self.dungeon:
            raise RuntimeError("Engine not initialized. Call setup() first.")

        new_position = self.dungeon.adjacent_position(self.state.player.position, direction)
        if not self.dungeon.in_bounds(new_position):
            return False

        self.state.player.position = new_position
        room = self.dungeon.room_at(new_position)
        room.visited = True
        return True

    def resolve_current_room(self) -> str:
        if not self.state or not self.dungeon:
            raise RuntimeError("Engine not initialized. Call setup() first.")

        room = self.dungeon.room_at(self.state.player.position)
        if room.room_type is RoomType.MONSTER and room.monster is not None:
            return "monster"
        if room.room_type is RoomType.CHEST and not room.chest_opened:
            return "chest"
        if room.room_type is RoomType.EXIT:
            return "exit"
        return "empty"

    def grant_chest_reward(self) -> Spell:
        if not self.state:
            raise RuntimeError("Engine not initialized. Call setup() first.")

        ions = self.data.load_ions()
        _, spell_pool = self.data.for_mode(self.config.mode, ions)
        reward = Spell(ion=self.rng.choice(spell_pool))
        self.state.player.add_spell(reward)
        return reward

    def _generate_defeatable_monster(self) -> Monster:
        if not self.state:
            raise RuntimeError("Engine not initialized. Call setup() first.")

        available_spells = self.state.player.available_spells()
        if not available_spells:
            # Fallback if player has no spells
            ion = self.rng.choice(self.monster_pool)
            return Monster(ions=[ion], name=ion.name)

        cation_charges = [s.charge for s in available_spells if s.charge > 0]
        anion_charges = [s.charge for s in available_spells if s.charge < 0]

        allowed_net_charges: set[int] = set()

        if self.config.mode is GameMode.ANION:
            if cation_charges:
                pos_sums = get_possible_subset_sums(cation_charges)
                allowed_net_charges = {-p for p in pos_sums}
        elif self.config.mode is GameMode.CATION:
            if anion_charges:
                neg_sums = get_possible_subset_sums(anion_charges)
                allowed_net_charges = {-n for n in neg_sums}
        else:  # Mixed mode
            if cation_charges:
                pos_sums = get_possible_subset_sums(cation_charges)
                allowed_net_charges.update({-p for p in pos_sums})
            if anion_charges:
                neg_sums = get_possible_subset_sums(anion_charges)
                allowed_net_charges.update({-n for n in neg_sums})

        if not allowed_net_charges:
            # Fallback
            ion = self.rng.choice(self.monster_pool)
            return Monster(ions=[ion], name=ion.name)

        # Find candidates (single ion or pair of ions summing to one of the target charges)
        candidates: list[Monster] = []
        for ion in self.monster_pool:
            if ion.charge in allowed_net_charges:
                candidates.append(Monster(ions=[ion], name=ion.name))

        # Check dual-ion combinations for variety if candidates are few
        if len(candidates) < 10:
            for i in range(len(self.monster_pool)):
                for j in range(i, len(self.monster_pool)):
                    ion1 = self.monster_pool[i]
                    ion2 = self.monster_pool[j]
                    net = ion1.charge + ion2.charge
                    if net in allowed_net_charges:
                        candidates.append(Monster(ions=[ion1, ion2], name=f"{ion1.name} & {ion2.name}"))

        if not candidates:
            # Fallback
            ion = self.rng.choice(self.monster_pool)
            return Monster(ions=[ion], name=ion.name)

        return self.rng.choice(candidates)

    def start_encounter(self) -> EncounterState:
        if not self.state or not self.dungeon:
            raise RuntimeError("Engine not initialized. Call setup() first.")

        room = self.dungeon.room_at(self.state.player.position)
        if room.room_type is not RoomType.MONSTER:
            raise ValueError("No monster in current room")

        # Swap the monster with a dynamically generated defeatable one
        old_charge = abs(room.monster.net_charge) if room.monster is not None else 0
        new_monster = self._generate_defeatable_monster()
        room.monster = new_monster
        self.state.total_required_charge = self.state.total_required_charge - old_charge + abs(new_monster.net_charge)

        return EncounterState.from_monster(room.monster)

    def cast_spell(self, encounter: EncounterState, spell_index: int):
        if not self.state:
            raise RuntimeError("Engine not initialized. Call setup() first.")

        spell = self.state.player.mark_spell_used(spell_index)
        return self.resolver.cast_spell(encounter, spell, self.state.player)

    def is_run_over(self) -> bool:
        if not self.state or not self.dungeon:
            raise RuntimeError("Engine not initialized. Call setup() first.")

        player = self.state.player
        at_exit = player.position == self.dungeon.exit_position
        no_spells = len(player.available_spells()) == 0
        dead = not player.is_alive()
        return dead or no_spells or at_exit

    def finalize_score(self) -> float:
        if not self.state:
            raise RuntimeError("Engine not initialized. Call setup() first.")

        required = self.state.total_required_charge
        if required <= 0:
            self.state.score_percent = 0.0
            return 0.0

        raw = (self.state.player.total_charge_offset / required) * 100
        self.state.score_percent = max(0.0, min(100.0, raw))
        return self.state.score_percent

    def _compute_total_required_charge(self) -> None:
        if not self.state or not self.dungeon:
            return

        total = 0
        for room in self.dungeon.rooms.values():
            if room.monster is not None:
                total += abs(room.monster.net_charge)
        self.state.total_required_charge = total
