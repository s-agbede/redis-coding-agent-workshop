# The team's way: Redis Agent Playbook

**12-minute demo, 5 minutes for you.** Redis Agent Memory learned how *you* like code written. How the *team* validates a report is a different kind of knowledge.

## From personal to organisational

A preference can be learned from one person's conversations. A team rule shouldn't be. It's written down, reviewed, **published once**, and every agent that uses it should get the same version.

**Redis Agent Playbook** does that for agent skills:

- **Publish:** a skill folder with a `SKILL.md` becomes a versioned Playbook entry.
- **Retrieve:** an agent searches the Playbook with its task and gets the relevant skill.
- **Share:** every agent, in every project, gets the same version.

## Demo: publish once

Open the team's [report-validation skill](../../skills/report-validation/SKILL.md). It's five rules: use `Decimal` for amounts, report every problem, write each error as `row <n>: <problem>`, and so on.

The instructor runs `/publish-skill`. This is the one copy the whole room uses; your workspace already knows its ID and only needs read access. Run `/skills` to see it.

**Predict:** does publishing it put it into the agent's next request?

## Demo: switch on Playbook

No: the agent has to retrieve it. In `agent.py:flags`, set `PLAYBOOK = True`. That turns on `agent.py:playbook`:

```python
if PLAYBOOK:
    skill = services.playbook.retrieve(task, min_score=SKILL_MIN_SCORE)
```

Playbook search always returns its closest skills, even for a task that has nothing to do with them, so the agent only uses one that scores at least `SKILL_MIN_SCORE` (0.7) for this task. `agent.py:request` then adds it to the request with its name and version, so you can always tell which procedure the agent followed.

Save, type `exit`, start again, and try two tasks:

```text
Write a FizzBuzz function.
```

The terminal says *Team procedure: none for this task*: FizzBuzz has nothing to do with report validation.

```text
What are our rules for validating report rows?
```

This time it says *Team procedure: report-validation, version 1*, and `/view-context` shows the procedure in the second message.

**Optional:** the instructor adds a rule to the skill and runs `/publish-skill` again. It becomes version 2 of the same entry, and your next `/skills` shows it.

## Your turn (5 minutes)

1. `/skills`. **Look for:** report-validation, with the same version as the instructor's screen.
2. In `agent.py:flags`, set `PLAYBOOK = True`. Save, type `exit`, and start again.
3. Ask for a FizzBuzz function. **Look for:** *Team procedure: none for this task*.
4. Ask about the rules for validating report rows. **Look for:** *Team procedure: report-validation*, and the procedure in `/view-context`.

Next: [trust, but verify](06-verify.md).
