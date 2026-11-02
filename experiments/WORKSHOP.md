# Give your coding assistant memory across sessions

**Part 2 exercise · 25 minutes.** Tell the completed coding assistant a preference,
inspect what Redis Agent Memory extracts, then ask a fresh session to use it.
You will run and inspect the supplied Python SDK integration.

By the end, show three separate pieces of evidence: the stored interaction, the
extracted preference, and the preference retrieved for a new answer.

## Before you start

Use a terminal at the root of the `iris` repository checkout. The instructor must
provide a configured Agent Memory service with the enabled `user_preference` type,
model access, and the root `.env` settings. Do not paste credentials into prompts.
This exercise runs from the repository checkout; it is not yet packaged into the
Part 1 browser workspace.

The supplied program uses the completed agent from Part 1. For this first memory
exercise, tool execution is disabled: the assistant explains commands but does not
run them. Your learner `agent.py` and project instruction files remain unchanged.

## 1. Start with a fresh identity — 3 minutes

Run these commands once in the same terminal you will use for the exercise:

```bash
export IRIS_LAB_OWNER="learner-$(uv run --group iris python -c 'from uuid import uuid4; print(uuid4().hex)')"
export IRIS_LAB_SESSION="teach-$IRIS_LAB_OWNER"
```

Keep these variables for the remaining steps. Each learner gets a different
synthetic identity so old experiments do not influence the results. These labels
and search filters demonstrate memory selection; they are not access controls.

Before teaching a preference, try recalling one:

```bash
uv run --group iris python -m experiments.iris_memory recall --owner "$IRIS_LAB_OWNER" --prompt 'How should I initialise a new Python project and manage dependencies? Give me a short answer.'
```

**Expected:** `No custom preferences retrieved yet.` The command exits without
calling the model. This establishes an empty memory baseline for your test identity.
If it returns memories, stop and create a new identity before continuing.

## 2. State a preference — 5 minutes

```bash
uv run --group iris python -m experiments.iris_memory teach --owner "$IRIS_LAB_OWNER" --session "$IRIS_LAB_SESSION" --prompt 'Use uv for Python projects, and ask before adding dependencies.'
```

Inspect `session_memory.events` in the output. Find:

- The `USER` event containing your original words.
- The `ASSISTANT` event containing the model's actual reply.
- Their shared session ID and their separate roles and timestamps.

**Checkpoint:** both messages reached the service. An assistant saying it will
remember something is not proof that a long-term memory exists.

Open `experiments/iris_memory.py` and locate the two `add_session_event` calls in
`run_turn`. Trace user event → model call → assistant event. The SDK records text
without truncation in this exercise. No code creates a long-term memory directly.

## 3. Inspect automatic extraction — 6 minutes

```bash
uv run --group iris python -m experiments.iris_memory inspect --owner "$IRIS_LAB_OWNER" --session "$IRIS_LAB_SESSION"
```

`session_memory` shows the conversation; `retrieval.items` shows long-term memories.
Extraction runs in the background. If `items` is empty, wait for the instructor's
configured extraction interval, then run **inspect** again. Do not repeat **teach**
just to trigger another check. If no memory appears after two configured intervals,
ask the instructor to investigate and use the labelled recorded example meanwhile.

Find a memory with `memoryType: user_preference`. Inspect its text and attributes:

| Field | What to check |
| --- | --- |
| `preference` | Does it preserve both using uv and asking before adding dependencies? |
| `scope` | Does it preserve the Python-project condition? |
| `replaces` | Is it empty for this first preference? |

Wording may vary. Record any omission or extra assumption rather than treating the
example as the required literal response. Treat `replaces` as unverified metadata;
this integration does not use it to delete or override other memories.

## 4. Ask a fresh session — 6 minutes

The previous command has already exited. Run the same question as your baseline:

```bash
uv run --group iris python -m experiments.iris_memory recall --owner "$IRIS_LAB_OWNER" --prompt 'How should I initialise a new Python project and manage dependencies? Give me a short answer.'
```

Do not provide `--session`: the program creates a new session ID. It starts with
no old conversation, retrieves preferences for the same owner, and adds those
records to the model's context.

**Check all three:**

1. The new `session` differs from your teaching session.
2. `retrieval.items` contains the preference you inspected.
3. The answer recommends uv and acknowledges asking before adding dependencies.

If retrieval succeeds but the answer ignores it, record a behaviour failure. If
retrieval is empty, investigate extraction and search before judging the model.
The answer alone cannot establish that retrieval worked.

This demonstrates recall across processes using the same agent implementation.
It does not demonstrate a second agent implementation or actual enforcement of
permission before installing a dependency.

## 5. Explain the result — 5 minutes

Show a partner the original message, extracted memory and retrieved record. Explain
where the memory entered the new model request. Each command saves a JSON report
and prints its path under `output/iris-memory/`.

Discuss:

- What would be lost if we recorded only the assistant's response?
- How does retrieving a preference differ from loading project instructions?
- Which evidence establishes extraction, retrieval and behaviour respectively?

<details>
<summary>Compare your explanation</summary>

The original user statement is direct evidence of their preference. An assistant
may omit, reinterpret or merely acknowledge it. The memory service extracts useful
information from the recorded events; the application retrieves it and supplies it
to a fresh model request. This is external context, not model retraining.

Instruction files remain useful for deliberately maintained project rules. This
exercise shows another mechanism for capturing and recalling stated preferences.
A memory's presence does not prove it was retrieved, and retrieval does not prove
that an assistant followed it.

</details>

Stop here for the participant exercise. Project exceptions, corrections and the
observed limits of `replaces` belong in the [instructor discussion](FACILITATOR.md).
