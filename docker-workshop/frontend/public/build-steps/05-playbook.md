---
title: The team's way: Redis Agent Playbook
editorFile: agent.py
---
**12-minute demo, 5 minutes for you.** Redis Agent Memory learned how *you* like code written. How the *team* validates a report is a different kind of knowledge.

## From personal to organisational

A preference can be learned from one person's conversations. A team rule shouldn't be. It's written down, reviewed, **published once**, and every agent that uses it should get the same version.

**Redis Agent Playbook** does that for agent skills:

- **Publish:** a skill folder with a `SKILL.md` becomes a versioned Playbook entry.
- **Retrieve:** an agent searches the Playbook with its task and gets the relevant skill.
- **Share:** every agent, in every project, gets the same version.

## Demo: publish once

Open the team's [report-validation skill](/skills/report-validation/SKILL.md). It's five rules: use `Decimal` for amounts, report every problem, write each error as `row <n>: <problem>`, and so on.

The instructor runs `/publish-skill`. This is the one copy the whole room uses; your workspace already knows its ID and only needs read access.

**Predict:** does publishing it put it into the agent's next request?

No. The agent has to retrieve it and add it, just like a preference:

```python
def skill_context(skill: PublishedSkill | None) -> str:
    if skill is None:
        return ''
    return f'Team procedure from Redis Agent Playbook ({skill.name}, version {skill.version}):\n{skill.instructions}'
```

The name and version travel with the rules, so you can always tell which procedure the agent followed.

**Optional:** the instructor adds a rule to the skill and runs `/publish-skill` again. It becomes version 2 of the same entry, and your next `/skills` shows it.

## Your turn (5 minutes)

Type `exit`, then:

```bash
cp solutions/steps/03-playbook.py agent.py
uv run --group iris python main.py
```

Read `skill_context` in `agent.py`. Then run `/skills`. **Look for:** report-validation, with the same version as the instructor's screen.

Next: [trust, but verify](/build?lesson=06-verify.md).
