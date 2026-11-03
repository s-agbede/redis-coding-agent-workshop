from decimal import Decimal, InvalidOperation


def validate_report(rows: list[dict[str, str]]) -> list[str]:
    """Return the problems found in a report's rows.

    Args:
        rows: Report rows, each a dict of strings.

    Returns:
        One ``row <n>: <problem>`` string per problem; empty when the report is valid.
    """
    errors: list[str] = []
    seen: set[str] = set()
    for number, row in enumerate(rows, start=1):
        record_id = row.get("record_id", "")
        if not record_id:
            errors.append(f"row {number}: missing record_id")
        elif record_id in seen:
            errors.append(f"row {number}: duplicate record_id {record_id}")
        seen.add(record_id)
        if "amount" not in row:
            errors.append(f"row {number}: missing amount")
            continue
        try:
            amount = Decimal(row["amount"])
        except InvalidOperation:
            errors.append(f"row {number}: amount is not a number")
            continue
        if not amount.is_finite() or amount < 0:
            errors.append(f"row {number}: amount can't be negative")
    return errors
