from validator import validate_report


def test_valid_rows_have_no_errors() -> None:
    rows = [{"record_id": "A001", "amount": "12.50"}, {"record_id": "A002", "amount": "0"}]
    assert validate_report(rows) == []


def test_negative_amount_is_reported_with_its_row_number() -> None:
    rows = [{"record_id": "A001", "amount": "12.50"}, {"record_id": "A002", "amount": "-3"}]
    [error] = validate_report(rows)
    assert error.startswith("row 2:")


def test_amount_that_is_not_a_number_is_reported() -> None:
    [error] = validate_report([{"record_id": "A001", "amount": "abc"}])
    assert error.startswith("row 1:")


def test_missing_fields_are_reported() -> None:
    errors = validate_report([{"record_id": "A001"}, {"amount": "5"}])
    assert [error.split(":")[0] for error in errors] == ["row 1", "row 2"]


def test_duplicate_record_id_is_reported_on_the_later_row() -> None:
    rows = [{"record_id": "A001", "amount": "1"}, {"record_id": "A001", "amount": "2"}]
    [error] = validate_report(rows)
    assert error.startswith("row 2:") and "duplicate" in error


def test_every_problem_is_reported_not_just_the_first() -> None:
    assert len(validate_report([{"record_id": "", "amount": "-1"}])) == 2
