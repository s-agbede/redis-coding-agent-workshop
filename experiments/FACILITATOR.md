# Facilitate the first Iris memory exercise

Allow 25 minutes within the 90-minute Part 2 workshop. Start with the completed
Part 1 agent and use [the participant exercise](WORKSHOP.md). Learners run and inspect
the SDK integration; this is not yet an exercise where they implement it themselves.

## Prepare the session

- Provide the full `iris` repository checkout with uv and model access. The current
  Part 1 browser workspace preparer does not copy `experiments/`; run this lab from
  the repository checkout until Part 2 packaging is implemented.
- Configure root `.env` with the existing model settings plus `AGENT_MEMORY_URL`,
  `AGENT_MEMORY_STORE_ID`, and `AGENT_MEMORY_API_KEY`. Keep credentials off slides.
- Verify that `user_preference` is enabled with `preference`, `scope`, and `replaces`
  fields. Record the actual extraction cadence and tell learners how long to wait.
- Rehearse the commands using a fresh synthetic owner. Run
  `uv run --group iris pytest tests/test_iris_memory.py -q` for integration checks;
  these substitute service responses and do not evaluate live extraction.
- Give learners isolated service credentials/stores where required. A freely chosen
  owner ID plus a search filter is not authentication or authorization.

## Observe the learning checkpoints

| Stage | Evidence | Failure to distinguish |
| --- | --- | --- |
| Capture | Original USER and actual ASSISTANT events | Assistant output alone can omit the preference |
| Extraction | A generated user_preference with preserved meaning | A saved conversation is not an extracted memory |
| Retrieval | That memory appears in the fresh run's retrieval.items | A good answer might be produced without memory |
| Behaviour | Answer respects tooling and approval preferences | Retrieved context is not guaranteed compliance |

The original source code records text-only turns through the completed loop. It
omits system prompts, file contents, tool requests and tool results. Discuss this
boundary before proposing learning from debugging outcomes.

## Recorded fallback

The files in `fixtures/` are recorded live SDK results from 21 October 2026 using
synthetic preferences. They are supplied evidence, not a live service fallback:

- `recorded-extraction.json`: original user and assistant events plus the extracted
  preference from the first experiment.
- `recorded-recall.json`: a fresh session's retrieved memory and actual answer.
- `recorded-scope-correction.json`: extracted records after a project exception and
  a dependency-approval correction, including imperfect replacement metadata.

If the service is unavailable or extraction does not complete after two configured
intervals, show the first two files explicitly as **recorded examples**. Ask learners
to trace the same evidence. Do not insert the desired memory and describe it as
successful automatic extraction. Record that the live checkpoint remains incomplete.

## Instructor discussion on exceptions and corrections

After the core exercise, present the previously tested statements:

1. General preference: use uv for Python projects and ask before adding dependencies.
2. Exception: preserve Poetry for legacy-ledger only; keep uv elsewhere.
3. Correction: no approval needed for disposable prototypes; still ask in production.

In one live trial, automatic extraction preserved the exception and updated the
original preference. Four fresh-session answers selected Poetry for legacy-ledger,
uv for another project, no approval for a disposable prototype, and approval for
production. An unrelated-owner search returned no records. These are observations
from one trial; the owner check tests filtering, and the answers do not test actual
tool permission enforcement.

The exception's `replaces` attribute nevertheless quoted the entire initial
preference, including dependency approval. Show this in the recorded fixture.
Ask learners whether a consumer should delete that entire preference. It should
not: the metadata is broader than the stated exception. The current service setup
cannot edit the extraction prompt, so the exercise documents this limitation.

The integration passes retrieved records to the model as contextual data and does
not interpret `replaces` as a deletion or precedence instruction. The model can
still be influenced by that field; this is not a conflict-resolution guarantee.
Current explicit instructions and relevant project scope require separate checks.
Do not make automated correction handling a required learner success criterion.
