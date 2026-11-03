# Trust, but verify

**6-minute demo, 5 minutes for you.** All three sources guide one real task. The tests decide whether it worked.

## Demo: one task, three sources

The project has an unfinished `validator.py` and a set of tests in `tests/`. With all three flags on, the instructor starts a fresh session and asks:

```text
Implement validate_report in validator.py and make the tests pass.
```

The agent reads the code and tests, writes the function, and asks to run the tests. Approve it.

`/view-context` shows where each piece of knowledge came from:

| In the request | Source | Owner |
| --- | --- | --- |
| "Python with type hints" | `AGENTS.md` | The project |
| "What you know about this user's preferences" | Redis Agent Memory | You |
| "Team procedure from Redis Agent Playbook" | Redis Agent Playbook | The organisation |

Then `/verify` runs the tests yourself. The agent saying "tests pass" is a claim; the test run is the evidence.

## Your turn (5 minutes)

**1.** Start fresh and give the agent the real task. Approve the test run when it asks:

```text
/new-session
```

```text
Implement validate_report in validator.py and make the tests pass.
```

**2.** See where each piece of knowledge came from:

```text
/view-context
```

**Look for:** all three sources.

**3.** Check the work yourself:

```text
/verify
```

**Look for:** "Tests passed."

**4.** Open `project/validator.py`. Find one rule that came from the team procedure (`Decimal`? the error format?) and check for your Google-style docstring.

<details>
<summary>Out of time?</summary>

```bash
cp solutions/validator.py project/validator.py
```

This is a reference answer, not the agent's.

</details>

## Three sources, three owners

| Knowledge | Today's example | Home |
| --- | --- | --- |
| Project convention | Python with type hints | `AGENTS.md`, reviewed with the code |
| Personal preference | Google-style docstrings | Redis Agent Memory, learned from your conversations |
| Team rule | How reports are validated | Redis Agent Playbook, published and versioned |

**Discussion:** pick one of each from your own team. Who should be able to read a memory? How would you correct or delete one? Who approves publishing a procedure?
