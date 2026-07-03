from __future__ import annotations

from pathlib import Path
import unittest

from game.data import CsvIonRepository
from game.enums import GameMode, IonPoolType


class TestData(unittest.TestCase):
    def test_parse_charge_supports_signed_values(self) -> None:
        self.assertEqual(CsvIonRepository.parse_charge("+1"), 1)
        self.assertEqual(CsvIonRepository.parse_charge("-4"), -4)


    def test_parse_charge_rejects_zero(self) -> None:
        with self.assertRaises(ValueError):
            CsvIonRepository.parse_charge("0")


    def test_repository_loads_standard_ions(self) -> None:
        repo = CsvIonRepository(Path("ions.csv"), pool_type=IonPoolType.STANDARD)
        ions = repo.load_ions()
        self.assertTrue(ions)
        self.assertTrue(all(ion.ion_type == "standard" for ion in ions))


    def test_for_mode_filters_sign_pools(self) -> None:
        repo = CsvIonRepository(Path("ions.csv"), pool_type=IonPoolType.STANDARD)
        ions = repo.load_ions()

        monster_pool, spell_pool = repo.for_mode(GameMode.ANION, ions)
        self.assertTrue(all(ion.charge < 0 for ion in monster_pool))
        self.assertTrue(all(ion.charge > 0 for ion in spell_pool))


if __name__ == "__main__":
    unittest.main()
