from __future__ import annotations

from dataclasses import dataclass

from .models import Monster, Player, Spell


@dataclass
class CastResult:
    defeated: bool
    damage: int
    offset_applied: int
    remaining_charge: int
    message: str


@dataclass
class EncounterState:
    monster: Monster
    initial_charge: int
    remaining_charge: int
    is_complete: bool = False

    @classmethod
    def from_monster(cls, monster: Monster) -> "EncounterState":
        charge = monster.net_charge
        return cls(monster=monster, initial_charge=charge, remaining_charge=charge)


class EncounterResolver:
    def cast_spell(self, state: EncounterState, spell: Spell, player: Player) -> CastResult:
        """Apply one spell cast and mutate encounter/player state."""
        if state.is_complete:
            return CastResult(
                defeated=True,
                damage=0,
                offset_applied=0,
                remaining_charge=0,
                message="Monster already defeated.",
            )

        cast_charge = spell.charge
        remaining = state.remaining_charge

        if self._is_opposite_sign(remaining, cast_charge):
            offset = min(abs(cast_charge), abs(remaining))
            new_remaining = remaining + cast_charge

            if self._is_neutralized(new_remaining) or self._is_overcharged(remaining, cast_charge):
                excess = abs(new_remaining)
                if excess > 0:
                    player.take_damage(excess)
                state.remaining_charge = 0
                state.is_complete = True
                player.total_charge_offset += offset
                player.monsters_defeated += 1
                return CastResult(
                    defeated=True,
                    damage=excess,
                    offset_applied=offset,
                    remaining_charge=0,
                    message="Monster defeated.",
                )

            state.remaining_charge = new_remaining
            player.total_charge_offset += offset
            return CastResult(
                defeated=False,
                damage=0,
                offset_applied=offset,
                remaining_charge=new_remaining,
                message="Spell reduced monster charge.",
            )

        damage = abs(cast_charge)
        player.take_damage(damage)
        return CastResult(
            defeated=False,
            damage=damage,
            offset_applied=0,
            remaining_charge=state.remaining_charge,
            message="Wrong sign cast. Monster unaffected.",
        )

    @staticmethod
    def _is_opposite_sign(a: int, b: int) -> bool:
        return (a > 0 and b < 0) or (a < 0 and b > 0)

    @staticmethod
    def _is_neutralized(value: int) -> bool:
        return value == 0

    @staticmethod
    def _is_overcharged(previous: int, cast: int) -> bool:
        return abs(cast) > abs(previous)
