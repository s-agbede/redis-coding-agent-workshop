# Facilitate the memory workshop

Use the [90-minute schedule](/WORKSHOP.md). Each section is your demo followed by five minutes of attendee hands-on. Complete the setup and rehearsal below before delivery.

## Before the session

**Services.** Provision Redis Agent Memory and Redis Agent Playbook. Confirm the existing `user_preference` extraction works with the commenting preference; do not plan to change extraction configuration during class.

**Publish the team skill once, in advance.** On your instructor machine, with a Playbook key that can create, publish and read, and **without** `PLAYBOOK_SKILL_ID` set:

```bash
uv run --group iris python main.py --agent solutions/steps/03-playbook.py
```

Run `/publish-skill` and note the `entry_id`. That ID stays the same for every later publication of the skill, including the live one and any version 2.

**Attendee workspaces.** Each attendee gets an isolated workspace with:

- model settings (`AGENT_API_KEY`, `AGENT_MODEL`, optional `AGENT_BASE_URL` for an approved gateway);
- `AGENT_MEMORY_URL`, `AGENT_MEMORY_STORE_ID`, `AGENT_MEMORY_API_KEY`;
- `PLAYBOOK_DATA_PLANE_URL`, `PLAYBOOK_PLAYBOOK_ID`, a **read-only** `PLAYBOOK_API_KEY`, and `PLAYBOOK_SKILL_ID` set to your entry ID.

Each workspace persists its own synthetic owner identity, so new sessions keep the owner. Do not show keys on screen.

For the supplied Docker setup, a Playbook at `127.0.0.1:9301` on the host is reached as `WORKSHOP_PLAYBOOK_DATA_PLANE_URL=http://host.docker.internal:9301`.

**Rehearse** the full path in the browser workbench with real services, ideally with several attendees on one memory store at once. Measure extraction latency: the recall demo (about 10 minutes) must cover it.

## Running each section

Your own `agent.py` follows the same snapshots as the attendees. After each code change: save, `exit`, relaunch, `/status`.

- **Recap (0–4).** One picture: model asks, Python runs the tool, result returns. Ask today's question and show the four-source table. Attendees launch and run `/status`.
- **The amnesiac and notes on the desk (4–17).** State the preference, run the filename task, `/new-session`, `/view-context`: it is gone. Then the `AGENTS.md` edit, `/new-session`, `/view-context`: it survives. Land the point: files hold what someone *decides* to write down.
- **Capture (17–32).** Introduce Redis Agent Memory by name: session events, background extraction, typed long-term memories. Walk through `record_event` and the roles. Enable capture, restart, restate the preference and task, show `/events`. `/memories` may still be empty; say you will return to it. Attendees copy `01-capture.py`.
- **Recall (32–47).** Open with `/memories`, now populated, from your capture. Walk through `recall_preferences` (owner, not session) and `preference_context`. Enable recall, restart, run `missing_columns`, show the retrieved block in `/view-context`. Land the point: memory is context your application chooses to add. Attendees copy `02-recall.py`; their extraction ran during your demo.
- **Playbook (47–64).** Make the personal → organisational turn explicit. Introduce Redis Agent Playbook: publish, version, retrieve, share. Run `/publish-skill` live; it reconfirms the same entry. Walk through `skill_context`, enable Playbook, restart, `/skills`. Then `uv run --group iris python main.py --project project-review` and `/skills`: same source and version. Attendees copy `03-playbook.py` and run `/skills`.
- **Optional version 2.** Add a non-functional line to `skills/report-validation/SKILL.md`, for example "Name the contract rule each check implements in its comment." Run `/publish-skill`: Playbook records version 2 of the same entry. Ask the room to run `/skills` and see the new version. Do not change the functional rules: the checker and contract are fixed. Restore `SKILL.md` from git afterwards.
- **Verify (64–75).** `/new-session`, the validator task, `/view-context`: point to all three sources and their owners. `/verify` for the real exit status. Ask for one rule attributed to the procedure.
- **Discussion (75–85).** See below.

## Governance discussion

This audience will ask about controls. Prepare answers for your deployment; the SDKs expose operations you can point to, but confirm their behaviour before claiming it.

| Question | Point to |
| --- | --- |
| Who can read a memory? | The owner filter in recall selects records; it is not access control. Isolation comes from store and credential provisioning, and Redis Agent Memory namespaces. |
| Can we correct or delete what it learned? | Agent Memory `update_long_term_memory`, `bulk_delete_long_term_memories`, `delete_session_memory`. |
| Personal or sensitive data in memories? | Extraction works on what is captured. Decide what to capture; prompts asking the model to exclude content are not redaction. Use synthetic data today. |
| Who approves a procedure? | Playbook separates creating a version from publishing it; it also has proposal and withdrawal operations. Only the publisher's key needs write access. |
| How do changes roll out? | Consumers retrieve the current published version; source and version appear in every request for audit. |

## Troubleshooting

| Observation | Response |
| --- | --- |
| Preference absent from `/events` | It must be restated after capture is enabled, in the current session |
| Events present, `/memories` empty | Extraction is asynchronous; wait through the recall demo, then check configuration. Never insert a memory by hand and call it extraction |
| `/memories` populated, recall empty | Compare owner and memory type; do not broaden the filter to other attendees |
| `/skills` says no team skill selected | `PLAYBOOK_SKILL_ID` is missing from that workspace |
| `/skills` returns `null` | The entry is not published, or the ID belongs to another Playbook |
| Attendee runs `/publish-skill` | Refused as an instructor step; this is expected |
| Agent claims success but `/verify` fails | Paste the actual failure back; keep the checker unchanged |

Owner filters demonstrate selection, not authorisation. Use synthetic workshop content only.

## Pilot acceptance

A pilot attendee finishes `/verify` before minute 75, explains why history and file persistence differ, locates the recalled preference and the published procedure in an actual request, and names a skill-derived rule. Record where they needed help and whether the extraction wait was hidden by the recall demo.
