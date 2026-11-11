---
name: report-validation
description: Our team's rules for code that validates incoming report rows.
---

# Validating report rows

Example team procedure for this workshop. Follow these rules whenever you write or review code that validates report rows. A report is a list of rows, and each row is a dict of strings.

- Every row needs a non-empty `record_id` and an `amount`.
- Parse amounts with `decimal.Decimal`, never `float`. Amounts can't be negative.
- A `record_id` may appear only once in a report. Report a repeat as a duplicate, on the later row.
- Report every problem, not just the first. Return a list of error strings, empty when the report is valid.
- Write each error as `row <n>: <problem>`, counting rows from 1.
