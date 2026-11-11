---
name: unit-tests
description: How our team writes unit tests with pytest, covering test names, one behaviour per test, inputs, and what a test must never call.
---

# Writing unit tests

Example team procedure for this workshop. Follow it whenever you write or review unit tests.

- Use `pytest` with plain `assert` statements and functions named `test_<behaviour>`.
- Test one behaviour per test, and name the test after it, for example `test_negative_amount_is_rejected`.
- Write small, explicit inputs inside the test instead of sharing mutable fixtures between tests.
- Tests must not call the network, a real database or the clock; pass fakes or fixed values in.
- Cover the happy path, at least one invalid input, and an edge case such as an empty list.
