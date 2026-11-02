# Give your coding agent useful memory

**90 minutes. Part 2 of the coding agent workshop.** Extend a working coding agent with **Redis Agent Memory**, so it recalls a developer's preferences across sessions, and **Redis Agent Playbook**, so it retrieves a published team procedure. Then check the code it produces with an independent checker.

**Audience:** software engineers who have used AI agents a little but are not experts. Part 1 is recommended; the recap covers what is needed.

**The through-line:** what should a coding agent know, where does that knowledge come from, and who owns it? Each section adds a source with a wider owner: the conversation, the project, you, the organisation. The close: *three sources, three owners, each one checkable.*

## Schedule

Each section is an instructor demo followed by a five-minute *Your turn* card. Attendees copy a cumulative snapshot from `solutions/steps/` rather than typing code: the code is teaching material.

| Elapsed | Section | Demo | Your turn | Attendees confirm |
| --- | --- | --- | --- | --- |
| 0–4 | [Recap: what goes into the request](/build?lesson=01-recap.md) | 4 | — | Agent running; `/status` shows all capabilities disabled |
| 4–17 | [The amnesiac and notes on the desk](/build?lesson=02-forgetting.md) | 8 | 5 | Preference gone after `/new-session`; uv line in `AGENTS.md` survives |
| 17–32 | [Capture with Redis Agent Memory](/build?lesson=03-capture.md) | 10 | 5 | `/events` shows their exchange |
| 32–47 | [Recall in a fresh session](/build?lesson=04-recall.md) | 10 | 5 | `/memories` lists the preference; `/view-context` shows it retrieved |
| 47–64 | [The team's way: Redis Agent Playbook](/build?lesson=05-playbook.md) | 12 | 5 | `/skills` shows the instructor's published source and version |
| 64–75 | [Trust, but verify](/build?lesson=06-verify.md) | 6 | 5 | `/verify` passes; they name a rule from the procedure |
| 75–85 | Discussion | | | Governance; where each source fits in their team |
| 85–90 | Buffer | | | |

Capture and recall are separate blocks on purpose: attendees capture during block 3, and Redis Agent Memory extracts the preference in the background while the instructor demonstrates recall.

The instructor publishes the team skill **once**. Attendees only retrieve it, by the entry ID in `PLAYBOOK_SKILL_ID`, with read-only Playbook access.

## Learning outcomes

Attendees can:

- explain why a conversational preference disappears in a new session while a project file survives;
- describe how Redis Agent Memory stores session events, extracts long-term preferences in the background, and returns them through owner-scoped search;
- show that recalled memory is context the application chooses to add, not something the model remembers;
- explain how Redis Agent Playbook publishes a versioned procedure that many agents and projects retrieve identically;
- locate each knowledge source in an actual model request and judge generated code with independent evidence.

Keep the commenting preference out of `AGENTS.md` throughout, so recall evidence stays distinct from file persistence.

## Assets

- [Learner welcome](/docs/welcome.md)
- [Facilitator guide](/FACILITATOR.md)
- [Supplied skill](/skills/report-validation/SKILL.md)
- [Challenge contract](/challenge/CONTRACT.md)
- [Implementation notes](/IMPLEMENTATION.md)

Slides are labelled placeholders until slide design is done; teach from the lesson text.
