from __future__ import annotations

import random
from dataclasses import dataclass

from .enums import RoomType
from .models import Ion, Monster, Room


@dataclass
class Dungeon:
    width: int
    height: int
    rooms: dict[tuple[int, int], Room]
    start_position: tuple[int, int]
    exit_position: tuple[int, int]

    def room_at(self, position: tuple[int, int]) -> Room:
        return self.rooms[position]

    def in_bounds(self, position: tuple[int, int]) -> bool:
        x, y = position
        return 0 <= x < self.width and 0 <= y < self.height

    def adjacent_position(self, position: tuple[int, int], direction: str) -> tuple[int, int]:
        x, y = position
        direction_key = direction.lower().strip()
        if direction_key == "n":
            return x, y - 1
        if direction_key == "s":
            return x, y + 1
        if direction_key == "w":
            return x - 1, y
        if direction_key == "e":
            return x + 1, y
        raise ValueError(f"Unsupported direction: {direction}")


class DungeonFactory:
    def __init__(self, rng: random.Random | None = None) -> None:
        self.rng = rng or random.Random()

    def build_simple_dungeon(
        self,
        width: int,
        height: int,
        monster_pool: list[Ion],
        monster_room_count: int,
        chest_room_count: int,
    ) -> Dungeon:
        """Build a simple room grid with start/exit and random room assignments."""
        if width < 2 or height < 2:
            raise ValueError("Dungeon width and height must be at least 2")

        start = (0, 0)
        exit_pos = (width - 1, height - 1)
        rooms: dict[tuple[int, int], Room] = {}

        all_positions = [(x, y) for y in range(height) for x in range(width)]
        for position in all_positions:
            room_type = RoomType.EMPTY
            if position == start:
                room_type = RoomType.START
            elif position == exit_pos:
                room_type = RoomType.EXIT
            rooms[position] = Room(room_type=room_type, position=position)

        available = [pos for pos in all_positions if pos not in {start, exit_pos}]
        self.rng.shuffle(available)

        monster_positions = available[:monster_room_count]
        chest_positions = available[monster_room_count : monster_room_count + chest_room_count]

        for position in monster_positions:
            rooms[position].room_type = RoomType.MONSTER
            ion = self.rng.choice(monster_pool)
            rooms[position].monster = Monster(ions=[ion], name=ion.name)

        for position in chest_positions:
            rooms[position].room_type = RoomType.CHEST

        return Dungeon(
            width=width,
            height=height,
            rooms=rooms,
            start_position=start,
            exit_position=exit_pos,
        )
