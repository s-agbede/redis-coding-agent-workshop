"""Explicit instructor reference, never silently loaded by the learner agent."""

from decimal import Decimal, InvalidOperation


def validate_report(rows: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for index, row in enumerate(rows, start=1):
        prefix = f"row {index}: "
        # Missing fields prevent the report from supplying the agreed evidence.
        for field in ("record_id", "amount"):
            if field not in row:
                errors.append(prefix + f"missing {field}")
        if "record_id" in row:
            identifier = row["record_id"]
            # Blank identifiers cannot distinguish records; repeated ones are ambiguous.
            if not identifier.strip():
                errors.append(prefix + "empty record_id")
            else:
                if identifier in seen:
                    errors.append(prefix + "duplicate record_id")
                seen.add(identifier)
        if "amount" in row:
            # Decimal avoids binary float rounding; the contract excludes nonfinite values.
            try:
                amount = Decimal(row["amount"])
                valid = amount.is_finite() and amount >= 0
            except InvalidOperation:
                valid = False
            if not valid:
                errors.append(prefix + "invalid amount")
    return errors
