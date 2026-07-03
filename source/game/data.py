from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from .enums import GameMode, IonPoolType
from .models import Ion


REQUIRED_COLUMNS = ("Name", "Formula", "Charge", "Type")


@dataclass
class CsvIonRepository:
    csv_path: Path
    pool_type: IonPoolType = IonPoolType.STANDARD

    def load_ions(self) -> list[Ion]:
        """Load and validate ions from the configured CSV file."""
        if not self.csv_path.exists():
            raise FileNotFoundError(f"Ion CSV not found: {self.csv_path}")

        ions: list[Ion] = []
        with self.csv_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle, skipinitialspace=True)
            self._validate_headers(reader.fieldnames)
            for row_num, raw_row in enumerate(reader, start=2):
                row = {k.strip(): (v.strip() if v is not None else "") for k, v in raw_row.items() if k}
                ion = self._parse_ion_row(row, row_num)
                if self._include_ion(ion):
                    ions.append(ion)

        if not ions:
            raise ValueError("No ions found for selected pool type")
        return ions

    def for_mode(self, mode: GameMode, ions: list[Ion]) -> tuple[list[Ion], list[Ion]]:
        """Return (monster_pool, spell_pool) for the provided mode."""
        cations = [ion for ion in ions if ion.charge > 0]
        anions = [ion for ion in ions if ion.charge < 0]

        if mode is GameMode.ANION:
            return anions, cations
        if mode is GameMode.CATION:
            return cations, anions
        return ions[:], ions[:]

    @staticmethod
    def parse_charge(value: str) -> int:
        text = value.strip()
        if not text:
            raise ValueError("Charge value is empty")

        try:
            charge = int(text)
        except ValueError as exc:
            raise ValueError(f"Invalid charge format: {value!r}") from exc

        if charge == 0:
            raise ValueError("Charge cannot be zero")
        return charge

    def _validate_headers(self, fieldnames: list[str] | None) -> None:
        if fieldnames is None:
            raise ValueError("CSV appears to be empty")

        cleaned = [name.strip() for name in fieldnames]
        missing = [column for column in REQUIRED_COLUMNS if column not in cleaned]
        if missing:
            joined = ", ".join(missing)
            raise ValueError(f"CSV is missing required columns: {joined}")

    def _parse_ion_row(self, row: dict[str, str], row_num: int) -> Ion:
        try:
            name = row["Name"]
            formula = row["Formula"]
            charge = self.parse_charge(row["Charge"])
            ion_type = row["Type"].lower()
        except KeyError as exc:
            raise ValueError(f"Row {row_num} missing expected column: {exc.args[0]}") from exc
        except ValueError as exc:
            raise ValueError(f"Row {row_num} has invalid data: {exc}") from exc

        if not name or not formula or not ion_type:
            raise ValueError(f"Row {row_num} contains empty required values")
        if ion_type not in {"standard", "extended"}:
            raise ValueError(f"Row {row_num} has unsupported type: {ion_type}")

        return Ion(name=name, formula=formula, charge=charge, ion_type=ion_type)

    def _include_ion(self, ion: Ion) -> bool:
        if self.pool_type is IonPoolType.ALL:
            return True
        if self.pool_type is IonPoolType.STANDARD:
            return ion.ion_type == "standard"
        return ion.ion_type == "extended"
