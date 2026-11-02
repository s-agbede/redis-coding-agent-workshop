"""Run unchanged checks against a supplied validator path, without extra packages."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys
from typing import Callable
import unittest

Validator = Callable[[list[dict[str, str]]], list[str]]


def load_validator(path: Path) -> Validator:
    spec = importlib.util.spec_from_file_location("report_validator_under_test", path)
    if spec is None or spec.loader is None:
        raise ValueError(f"Cannot load validator: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.validate_report


def suite(validate: Validator) -> unittest.TestSuite:
    class ContractChecks(unittest.TestCase):
        def test_examples(self) -> None:
            fixtures = json.loads(Path(__file__).with_name("fixtures.json").read_text())
            for fixture in fixtures:
                with self.subTest(name=fixture["name"]):
                    self.assertEqual(validate(fixture["rows"]), fixture["errors"])

        def test_empty_report(self) -> None:
            self.assertEqual(validate([]), [])

        def test_amount_boundaries(self) -> None:
            for value in ("0", "-0", "1e2", "0.001", " 2 "):
                with self.subTest(valid=value):
                    self.assertEqual(validate([{"record_id": "a", "amount": value}]), [])
            for value in ("", "x", "-0.01", "NaN", "sNaN", "Infinity", "-Infinity"):
                with self.subTest(invalid=value):
                    self.assertEqual(validate([{"record_id": "a", "amount": value}]), ["row 1: invalid amount"])

        def test_id_rules(self) -> None:
            rows = [{"record_id": value, "amount": "1"} for value in ("a", "A", " a", "a", "a", "", "  ")]
            self.assertEqual(validate(rows), ["row 4: duplicate record_id", "row 5: duplicate record_id", "row 6: empty record_id", "row 7: empty record_id"])

        def test_order_and_invalid_row_id_participation(self) -> None:
            rows = [{"record_id": "a", "amount": "bad"}, {"record_id": "a"}, {"record_id": "", "amount": "-1"}]
            self.assertEqual(validate(rows), ["row 1: invalid amount", "row 2: missing amount", "row 2: duplicate record_id", "row 3: empty record_id", "row 3: invalid amount"])

        def test_preserves_input_and_accepts_extra_columns(self) -> None:
            rows = [{"record_id": "a", "amount": "1", "note": "synthetic"}]
            original = copy.deepcopy(rows)
            self.assertEqual(validate(rows), [])
            self.assertEqual(rows, original)

    return unittest.defaultTestLoader.loadTestsFromTestCase(ContractChecks)


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: check_contract.py PATH_TO_VALIDATOR")
    result = unittest.TextTestRunner(verbosity=2).run(suite(load_validator(Path(sys.argv[1]))))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
