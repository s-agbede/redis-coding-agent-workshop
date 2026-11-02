# Synthetic report validation contract

This is an instructional data-format exercise, not financial guidance. Inputs are already-parsed rows. Do not implement CSV parsing, rounding, currencies or database access.

Implement:

```python
def validate_report(rows: list[dict[str, str]]) -> list[str]: ...
```

Input keys and values are strings, as stated by the interface. Values outside that interface are outside this exercise. Do not mutate input. Empty input is valid and returns `[]`. Return all errors in row order, using one-based row numbers.

For each row, check in this exact order:

1. Missing `record_id`, then missing `amount`: `row N: missing FIELD` for each absent key. Extra keys are allowed.
2. If `record_id` is present, reject `''` or whitespace-only values with `row N: empty record_id`. Otherwise compare the exact string, case-sensitively, to all preceding nonempty IDs. Every later occurrence produces `row N: duplicate record_id`. Do not trim or rewrite nonempty IDs. A row's nonempty ID participates even if that row has another error.
3. If `amount` is present, parse its string with Python `decimal.Decimal`. A parsing failure, nonfinite value (`NaN`, infinity) or value below zero produces `row N: invalid amount`. Zero is valid. All finite nonnegative strings accepted by Decimal, including scientific notation, are accepted. Do not round or normalize inputs.

Continue checking present fields when another field is missing. Return only the error strings; no success messages. Comments should explain why checks exist, separately from this functional contract.

Examples are in [fixtures.json](fixtures.json). The unchanged [checker](check_contract.py) covers examples and additional boundaries. The active learner [validator](../project/validator.py) intentionally starts with NotImplementedError; [validator.py](validator.py) in this folder is the preserved starter template. The [reference](../solutions/validator.py) is an explicit instructor catch-up. The terminal command `/verify` checks the selected project validator; do not edit the checker or fixtures.
