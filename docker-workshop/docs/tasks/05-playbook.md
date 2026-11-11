# The team's way: Redis Agent Playbook

**12-minute demo, 5 minutes for you, then a 2-minute close.** Redis Agent Memory learned how *you* like code written. How the *team* validates a report, or what it says about customer data, is a different kind of knowledge.

## From personal to organisational

A preference can be learned from one person's conversations. A team rule shouldn't be. It's written down, reviewed, **published once**, and every agent that uses it should get the same version.

**Redis Agent Playbook** holds two kinds of team knowledge:

- **Skills:** an approved *procedure* for a task, such as how we validate a report. A skill folder with a `SKILL.md` becomes a versioned entry.
- **FAQs:** an approved *answer* to a question people keep asking, such as whether customer data may go in test fixtures.

Either way: an agent searches the Playbook with its task and gets only what's relevant, and every agent, in every project, gets the same published version.

## Demo: publish once

Open the team's skill, `skills/report-validation/SKILL.md` (click it to open it in the editor). It's five rules: use `Decimal` for amounts, report every problem, write each error as `row <n>: <problem>`, and so on.

The instructor runs `/publish-skill`. This is the one copy the whole room uses; your workspace only needs read access. The workshop's Playbook, **BofA Coding Agent Workshop**, also holds two more team skills, `safe-logging` and `unit-tests`, and four approved FAQs (on public AI tools, secrets, open-source licences and reviewing agent code). They are workshop examples, not real policy. Run `/skills` to see the skills.

**Predict:** does publishing it put it into the agent's next request?

## Demo: switch on Playbook

No: the agent has to retrieve it. In `agent.py:flags`, set `PLAYBOOK = True`. That turns on `agent.py:playbook`:

```python
if PLAYBOOK:
    skill = services.playbook.retrieve(task, min_score=SKILL_MIN_SCORE)
```

Playbook search always returns its closest skills, even for a task that has nothing to do with them, so the agent takes the best-fitting one only if it scores at least `SKILL_MIN_SCORE` (0.7) for this task. `agent.py:request` then adds it to the request with its name and version, so you can always tell which procedure the agent followed.

Save, type `exit`, start again, and try two tasks:

```text
Write a FizzBuzz function.
```

The terminal says *Team procedure: none for this task*: FizzBuzz has nothing to do with report validation.

```text
What are our rules for validating report rows?
```

This time it says *Team procedure: report-validation, version 1*, and `/view-context` shows the procedure in the second message.

## Demo: from conversations to a team answer

Skills are written on purpose. Many team answers start as questions people keep asking their agents. Earlier, everyone asked:

```text
Can I use real customer data in test fixtures?
```

Each agent answered in its own words, and none of those answers is approved. Redis Agent Playbook can **promote** the question into a team answer, with a person in charge of what's approved:

1. **Extraction:** Playbook reads finished sessions from Redis Agent Memory and drafts an FAQ **proposal**. The instructor opens the Iris console, **Playbook → Proposals**: one proposal, with the sessions it came from as **evidence**. The more people asked, the more evidence it has.
2. **Review:** the drafted answer is whatever the agents said. The instructor rewrites it to the approved answer, then chooses **Accept as draft FAQ**. It's now an FAQ entry, but **unpublished**: no agent gets it yet.
3. **Publish:** in **Entries**, the instructor publishes it. From now on every agent gets the same answer, with its version.

With `PLAYBOOK` on, `agent.py:playbook` also searches the published FAQs, and uses only those that score at least `FAQ_MIN_SCORE` (0.75) for this task. Ask it again, in your own words:

```text
Can I put real customer records in my test fixtures?
```

The terminal says *Team answer: Can I use real customer data in test fixtures?*, and `/view-context` shows "Approved team answers from Redis Agent Playbook".

Memory learned from *your* conversations for *you*. Promotion turns what *many* people asked into one answer the *team* approved. Nothing reaches other people's agents until someone publishes it.

## Your turn (5 minutes)

**1.** See what the team published:

```text
/skills
```

**Look for:** the team's three skills, each with its published version.

**2.** In `agent.py:flags`, switch the Playbook on:

```python
PLAYBOOK = True
```

Save, type `exit` in the terminal, then start the agent again:

```bash
uv run --group iris python main.py
```

**3.** Ask for something unrelated:

```text
Write a FizzBuzz function.
```

**Look for:** *Team procedure: none for this task*.

**4.** Ask about the team's rules:

```text
What are our rules for validating report rows?
```

**Look for:** *Team procedure: report-validation*, and the procedure in `/view-context`.

**5.** Once the instructor has published the team answer, ask the fixture question in your own words:

```text
Can I put real customer records in my test fixtures?
```

**Look for:** *Team answer: …*, and "Approved team answers from Redis Agent Playbook" in `/view-context`.

**Try your own:** each of these should pick a different piece of team knowledge. Check the terminal's *Team procedure* or *Team answer* line for each:

```text
What should I never put in a log message?
```

```text
Write unit tests with pytest for a slug function.
```

```text
Where should I keep the API key for this service?
```

## Close: three sources in one request

With all three flags on, the instructor starts a fresh session and asks:

```text
Show me a function that validates the rows of a report.
```

`/view-context` shows where each piece of knowledge came from:

| In the request | Source | Owner |
| --- | --- | --- |
| "Python with type hints" | `AGENTS.md` | The project |
| "What you know about this user's preferences" | Redis Agent Memory | You |
| "Team procedure from Redis Agent Playbook" | Redis Agent Playbook | The organisation |

**Discussion:** pick one of each from your own team. Who should be able to read a memory? How would you correct or delete one? Who approves publishing a procedure or an answer?
