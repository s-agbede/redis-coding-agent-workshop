# Give your coding agent useful memory

**90 minutes, Part 2 of the coding agent workshop.** Give a working coding agent **Redis Agent Memory**, so it remembers a developer's preferences across sessions, and **Redis Agent Playbook**, so it follows the team's published procedure and approved answers.

**Audience:** software engineers who have used AI agents a little. Part 1 helps; the recap covers what's needed.

**The question:** what should a coding agent know, where does that knowledge come from, and who owns it? Each section adds a source with a wider owner: the conversation, the project, you, the organisation.

## Schedule

Each section is an instructor demo followed by a few minutes of hands-on, about an hour of content in all. All the code is already in `agent.py`: each section switches on one flag (`CAPTURE`, `RECALL`, `PLAYBOOK`) and attendees read the lines it turns on, linked from the lesson.

| Elapsed | Section | Demo | Your turn |
| --- | --- | --- | --- |
| 0–3 | [Recap: what goes into the request](docs/tasks/01-recap.md) | 3 | — |
| 3–14 | [The amnesiac and notes on the desk](docs/tasks/02-forgetting.md) | 7 | 4 |
| 14–28 | [Capture with Redis Agent Memory](docs/tasks/03-capture.md) | 10 | 4 |
| 28–42 | [Recall in a fresh session](docs/tasks/04-recall.md) | 10 | 4 |
| 42–59 | [The team's way: Redis Agent Playbook](docs/tasks/05-playbook.md) | 12 | 5 |
| 59–61 | Close: three sources in one request | 2 | — |
| 61–80 | Discussion and questions | | |
| 80–90 | Buffer | | |

Extraction runs in the background while the instructor demonstrates recall, so attendees' preferences are ready by their next turn. The instructor publishes the team skill once; attendees only read it.

## The running example

| Knowledge | Example | Home |
| --- | --- | --- |
| Project convention | "Python with type hints." | `AGENTS.md` |
| Personal preference | "I like Google-style docstrings." | Redis Agent Memory |
| Team rule | How report rows are validated | Redis Agent Playbook |

The close: with all three switched on, one request carries all three, and `/view-context` shows where each came from.

## Assets

- [Learner welcome](docs/welcome.md) and [facilitator guide](FACILITATOR.md)
- [Team skill](skills/report-validation/SKILL.md) and the [project](project/AGENTS.md) the agent works in
- **Presenter deck:** [Give a Coding Agent Useful Memory](https://claude.ai/artifact/P3PvggzgEereLL3s1BcAEa), with speaker notes. Private until you share it.
