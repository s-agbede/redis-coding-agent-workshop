---
name: safe-logging
description: How our team adds log statements to code, covering logger setup, log levels, message format, and what must never be logged.
---

# Logging safely

Example team procedure for this workshop. Follow it whenever you add or review logging.

- Use the standard `logging` module with a module-level logger, never `print`.
- Never log personal data, account numbers or secrets. If an account number must appear, mask it to its last four digits, for example `****1234`.
- Log identifiers that support tracing, such as a request or record ID, not the record's contents.
- Use `info` for normal events, `warning` for something recoverable, and `exception` inside an `except` block so the traceback is kept.
- Write messages as a short event name plus fields, for example `logger.info("payment_validated record_id=%s", record_id)`, not f-strings.
