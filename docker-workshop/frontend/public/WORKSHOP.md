# Give your coding agent useful memory

**90 minutes, Part 2 of the coding agent workshop.** Give a working coding agent **Redis Agent Memory**, so it remembers a developer's preferences across sessions, and **Redis Agent Playbook**, so it follows the team's published procedure. Then check its work with the project's tests.

**Audience:** software engineers who have used AI agents a little. Part 1 helps; the recap covers what's needed.

**The question:** what should a coding agent know, where does that knowledge come from, and who owns it? Each section adds a source with a wider owner: the conversation, the project, you, the organisation.

## Schedule

Each section is an instructor demo followed by five minutes of hands-on. All the code is already in `agent.py`: each section switches on one flag (`CAPTURE`, `RECALL`, `PLAYBOOK`) and attendees read the lines it turns on, linked from the lesson.

| Elapsed | Section | Demo | Your turn |
| --- | --- | --- | --- |
| 0–4 | [Recap: what goes into the request](/build?lesson=01-recap.md) | 4 | — |
| 4–17 | [The amnesiac and notes on the desk](/build?lesson=02-forgetting.md) | 8 | 5 |
| 17–32 | [Capture with Redis Agent Memory](/build?lesson=03-capture.md) | 10 | 5 |
| 32–47 | [Recall in a fresh session](/build?lesson=04-recall.md) | 10 | 5 |
| 47–64 | [The team's way: Redis Agent Playbook](/build?lesson=05-playbook.md) | 12 | 5 |
| 64–75 | [Trust, but verify](/build?lesson=06-verify.md) | 6 | 5 |
| 75–85 | Discussion | | |
| 85–90 | Buffer | | |

Extraction runs in the background while the instructor demonstrates recall, so attendees' preferences are ready by their next turn. The instructor publishes the team skill once; attendees only read it.

## The running example

| Knowledge | Example | Home |
| --- | --- | --- |
| Project convention | "Python with type hints." | `AGENTS.md` |
| Personal preference | "I like Google-style docstrings." | Redis Agent Memory |
| Team rule | How report rows are validated | Redis Agent Playbook |

The final task: "Implement `validate_report` in `validator.py` and make the tests pass."

## Assets

- [Learner welcome](/docs/welcome.md) and [facilitator guide](/FACILITATOR.md)
- [Team skill](/skills/report-validation/SKILL.md) and the [project](/project/AGENTS.md) the agent works in
- **Presenter deck:** [Give a Coding Agent Useful Memory](https://claude.ai/artifact/P3PvggzgEereLL3s1BcAEa), with speaker notes. Private until you share it.
