---
title: Trust, but verify
editorFile: agent.py
---
**6-minute demo, 5 minutes for you.** All three sources guide one task. An independent checker decides whether the result is right.

## Demo: one task, three sources

The instructor starts a fresh session (`/new-session`) and asks:

```text
Implement validate_report in validator.py using the published report-validation procedure. Keep its supplied interface. Inspect relevant context and make the smallest change. Do not edit the independent checker, contract or fixtures. Explain the checks you ran and any uncertainty.
```

`/view-context` shows where each piece of knowledge came from:

| In the request | Source | Owner |
| --- | --- | --- |
| "Use uv for Python projects." under `Project instructions:` | `AGENTS.md` | The project |
| The commenting preference under `Retrieved preferences` | Redis Agent Memory | You |
| `Published procedure:` and `Published version:` | Redis Agent Playbook | The organisation |

The conversation contains only this task. Nothing from earlier sessions was replayed.

Then `/verify` runs the unchanged [checker](/challenge/check_contract.py) against the agent's `validator.py` and prints its real exit status. The agent saying "tests pass" is not evidence; the checker is.

[Diagram placeholder: project instructions, recalled preference and published procedure guide the request; an independent checker evaluates the edited code.]

## Your turn (5 minutes)

At `You >`:

1. `/new-session`, then paste the validator task above.
2. `/view-context`: **look for** all three sources in the latest request.
3. `/verify`: **look for** `Independent checker exit: 0`. If it fails, paste the actual failure back to the agent and check its repair.
4. Name one rule in `project/validator.py` that came from the published procedure, and check whether its comment explains *why*. The checker tests behaviour; only you can judge whether the preference was followed.

<details>
<summary>Out of time?</summary>

A reference validator lets you explore the contract. Using it is not an agent-generated result.

```bash
cp solutions/validator.py project/validator.py
uv run --group iris python challenge/check_contract.py project/validator.py
```

</details>

## Three sources, three owners

| Knowledge | Example from today | Home |
| --- | --- | --- |
| Project convention | Use uv | `AGENTS.md`, reviewed with the code |
| Personal preference | Explain each check in a comment | Redis Agent Memory, learned from your work |
| Organisational rule | How reports are validated | Redis Agent Playbook, published and versioned |

**Discussion:** pick one of each from your own team. Then: who should be able to read a memory, how would you correct or delete one, and who approves publishing a procedure?
