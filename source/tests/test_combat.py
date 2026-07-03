from __future__ import annotations

import unittest

from game.combat import EncounterResolver, EncounterState
from game.enums import Difficulty
from game.models import Ion, Monster, Player, Spell


def _build_player() -> Player:
    return Player.from_difficulty(Difficulty.EASY)


class TestCombat(unittest.TestCase):
    def test_exact_neutralization_defeats_without_damage(self) -> None:
        monster = Monster(ions=[Ion("ammonium", "NH4", 1, "standard")], name="ammonium")
        state = EncounterState.from_monster(monster)
        resolver = EncounterResolver()
        player = _build_player()

        result = resolver.cast_spell(state, Spell(Ion("chloride", "Cl", -1, "standard")), player)

        self.assertTrue(result.defeated)
        self.assertEqual(result.damage, 0)
        self.assertEqual(player.health, 12)


    def test_overcharge_defeats_and_deals_excess_damage(self) -> None:
        monster = Monster(ions=[Ion("ammonium", "NH4", 1, "standard")], name="ammonium")
        state = EncounterState.from_monster(monster)
        resolver = EncounterResolver()
        player = _build_player()

        result = resolver.cast_spell(state, Spell(Ion("sulfate", "SO4", -2, "standard")), player)

        self.assertTrue(result.defeated)
        self.assertEqual(result.damage, 1)
        self.assertEqual(player.health, 11)


    def test_wrong_sign_damages_player_and_monster_survives(self) -> None:
        monster = Monster(ions=[Ion("ammonium", "NH4", 1, "standard")], name="ammonium")
        state = EncounterState.from_monster(monster)
        resolver = EncounterResolver()
        player = _build_player()

        result = resolver.cast_spell(state, Spell(Ion("sodium", "Na", 1, "standard")), player)

        self.assertFalse(result.defeated)
        self.assertEqual(result.damage, 1)
        self.assertEqual(state.remaining_charge, 1)
        self.assertEqual(player.health, 11)


if __name__ == "__main__":
    unittest.main()
