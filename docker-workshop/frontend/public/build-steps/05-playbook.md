---
title: The team's way: Redis Agent Playbook
editorFile: agent.py
slides: /slides/04-playbook.md
---
**12-minute demo, 5 minutes for you.** Redis Agent Memory learned how *you* like code written. How the *team* must validate a report is a different kind of knowledge.

## From personal to organisational

A personal preference can be learned from one person's conversations. A team procedure should not be: it is authored, reviewed, **published once**, and versioned, and every agent that uses it should get the same version.

**Redis Agent Playbook** does this for agent skills:

- **Publish:** a skill folder (an Agent Skills package with a `SKILL.md`) becomes a versioned Playbook entry.
- **Retrieve:** an agent searches the Playbook for its task and loads the entry's current **published** version.
- **Share:** every consuming agent, in any project, gets the same procedure and version, with a source it can cite.

[Diagram placeholder: one published report-validation skill → many agents and projects, each retrieving the same source and version.]

## Demo: publish once

Open the supplied [report-validation skill](/skills/report-validation/SKILL.md) and its [contract](/challenge/CONTRACT.md). The skill says **what** the validator must check. Your recalled preference says **how** to explain those checks.

The instructor runs `/publish-skill`. Redis Agent Playbook confirms the entry ID and published version. This is the one publication the whole room uses; your workspace is configured with that entry's ID (`PLAYBOOK_SKILL_ID`) and only needs read access.

**Predict:** does publishing the skill automatically add it to the agent's next request?

No. The agent has to retrieve it and put it in context, just like a recalled preference:

```python
def skill_context(skill: PublishedSkill | None) -> str:
    if skill is None:
        return ''
    return (
        f'Published procedure: {skill.source}\n'
        f'Published version: {skill.version}\n'
        f'{skill.instructions}'
    )
```

Source, version and instructions stay together, so a reviewer can always tell which procedure, at which version, guided the agent.

## Demo: the same procedure in another project

The instructor starts the completed agent against a second project:

```bash
uv run --group iris python main.py --project project-review
```

`/skills` returns the **same** source and version. A second project gets the team's procedure without republishing it.

**Optional:** the instructor changes the procedure and runs `/publish-skill` again. Redis Agent Playbook records it as the next version of the same entry, and the next `/skills` in your workspace shows the new version.

## Your turn (5 minutes)

Type `exit`, then:

```bash
cp solutions/steps/03-playbook.py agent.py
uv run --group iris python main.py
```

Refresh the editor and read `skill_context`. Then at `You >`:

1. `/status`: **look for** all three capabilities enabled and a `team_skill` entry ID.
2. `/skills`: **look for** a `source` of the form `playbook://…/skills/<entry>/versions/<n>` that matches the instructor's screen.

`/skills` only inspects the procedure. It enters the model request when you give the agent a real task, in the next section. `/publish-skill` is an instructor step; your workspace retrieves.

Next: [trust, but verify](/build?lesson=06-verify.md).
