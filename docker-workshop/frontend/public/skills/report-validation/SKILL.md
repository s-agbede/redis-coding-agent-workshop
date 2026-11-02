---
name: report-validation
description: Implement or review a validator for the workshop's synthetic report rows using the team's fixed acceptance contract.
---

# Validate an incoming report

Local content revision: workshop-1. This label is not a Playbook publication version.

Use this procedure when asked to implement or review the workshop report validator. Inputs are already-parsed `list[dict[str, str]]`; output is `list[str]`. Preserve input and the supplied interface. Empty input is valid. Extra columns are allowed. Do not add a parser, service or dependency.

For every row in order, number it from one and apply all checks in this order:

1. Required keys are `record_id`, then `amount`. For each absent key append `row N: missing FIELD`.
2. If `record_id` exists but is empty or whitespace-only, append `row N: empty record_id`. Otherwise detect duplicates against earlier nonempty IDs using exact case-sensitive strings, without trimming. Each later occurrence appends `row N: duplicate record_id`. An ID participates even when its row has another error.
3. If `amount` exists, parse it with standard-library `decimal.Decimal`. Parsing failure, nonfinite values and values below zero append `row N: invalid amount`. Zero and any finite nonnegative Decimal-accepted string, including scientific notation, are valid. Do not round or normalize.

Check present fields even when another key is absent. Return all errors in the stated row/check order and no success messages. Values outside the declared string interface are outside this exercise.

Before editing, inspect the supplied validator signature and independent contract. Make the smallest coherent change in the validator. Keep contract, fixtures and checker unchanged. Run the unchanged independent checker and report its actual exit/result; if you could not run it, say so. Inspect one accepted and one rejected example and explain why. Preserve project instructions and relevant user preferences, including requested explanatory comments.

Publication packaging must be validated by the instructor. This folder supplies authored procedure content; it does not assume any particular service upload format.
