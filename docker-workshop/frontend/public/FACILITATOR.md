# Facilitate the memory workshop

Use the [schedule](/WORKSHOP.md) and the [presenter deck](https://claude.ai/artifact/P3PvggzgEereLL3s1BcAEa). Each section is your demo, then a few minutes for the room: about an hour of content. Each lesson in the browser guide also shows its section's slides, with **Focus mode** for presenting. After changing the deck, run `python3 scripts/render_slides.py` and `uv run python scripts/publish_docs.py`.

## Before the session

1. **Services.** Redis Agent Memory and Redis Agent Playbook, reachable from the attendee workspaces.
2. **Publish the team skill.** On your machine, with a Playbook key that can publish and no `PLAYBOOK_SKILL_ID` set:

   ```bash
   uv run --group iris python main.py
   ```

   Run `/publish-skill` and note the entry ID. Publishing again keeps the same ID.
3. **Attendee workspaces.** Each gets the model settings (`AGENT_API_KEY`, `AGENT_MODEL`, optional `AGENT_BASE_URL`), the three `AGENT_MEMORY_*` settings, and the Playbook settings with a read-only key plus `PLAYBOOK_SKILL_ID` set to your entry ID.
4. **Redis Insight** (panel menu → Redis Insight) shows the Iris preview's databases when you start the workbench with `bash scripts/workbench_with_iris_preview.sh`. For other Redis databases, set `INSIGHT_DB1_*` / `INSIGHT_DB2_*` (host, port, alias, password) in `.env`.
5. **Optional: self-host Agent Memory.** With a license, add `AGENT_MEMORY_LICENSE_FILE` and `COMPOSE_FILE=docker-compose.yml:docker-compose.selfhost.yml` to `.env` and run `bash start.sh`. The workshop then uses a local Agent Memory 0.7 (server, worker, Control Plane, Redis 8). Redis Insight shows its database, and the Agent Memory panel's **Store settings** tab shows retention, extraction cadence, summarization and exclusions, which helps the governance discussion. The images are linux/amd64, so Apple Silicon runs them under emulation; rehearse the timing.
6. **Rehearse** with real services, ideally with a few people on the same memory store.

## Running Memory and Playbook yourself (Iris on-prem preview)

Instead of the hosted services, the [Iris on-prem preview](https://github.com/redis-applied-ai/iris-onprem-preview) runs Agent Memory, Playbook, Lens and Context Gateway in a local Kubernetes cluster. It needs an Iris suite license (request it through the Iris license workflow) and suits rehearsal or a presenter demo; it listens on `127.0.0.1` only.

```bash
cd ~/Documents/Projects/iris-onprem-preview
install -m 600 /path/to/license.key .demo/licenses/iris.license
OPENAI_API_KEY=sk-... task up    # the key enables real extraction; omit it for a model-free start
task open                        # the Iris UI at http://127.0.0.1:18080
```

Then, in the workshop folder:

```bash
source scripts/use_iris_preview.sh publish    # your terminal: operator token, so /publish-skill works
uv run --group iris python main.py           # run /publish-skill, note the entry ID
source scripts/use_iris_preview.sh            # attendee view: read-only app keys
export PLAYBOOK_SKILL_ID=ent_...              # the entry ID you just published
```

The workshop's current SDK versions work with the preview. Recall filters on the custom `coding_preference` memory type, so the workshop needs its own store:

- `python3 scripts/iris_preview_store.py` creates the `coding-agent-workshop` store from `agent-memory/store.json` (with that type) and a key for it; `use_iris_preview.sh` then uses it.
- The preview ships with custom extraction switched off. Set `"custom_extraction": {"enabled": True}` and add a `custom_extraction` strategy next to `instruct` under `promote_session_memory` in the preview's `scripts/local/config.py`, then `task up` again.
- On a store without the type (for example the hosted one), remove the `memory_type` filter at `agent.py`'s Section 4 step, or recall finds nothing.

`task down` deletes the cluster and its data.

## Running it

Your `agent.py` follows the same flags as the room: each section switches one on in `handle`'s file. After each change: save, `exit`, relaunch.

- **Recap.** Model asks, Python runs the tool, the result goes back. Ask today's question.
- **The amnesiac.** "By the way, I like Google-style docstrings on my functions." Ask for the slug function; it gets the docstring. `/new-session`, ask for the same slug function, `/view-context`: the preference is gone. Have the agent add it to `AGENTS.md`, start a new session, and ask again: it works every time. Then walk through what that costs (manual, applies to everyone, only grows, never expires) and name the three jobs: extraction, lifecycle, retrieval. Have the agent take the line back out.
- **Capture.** Name Redis Agent Memory. Open Store settings in the Agent Memory panel first: retention, extraction, the `coding_preference` prompt, and the sensitive-data exclusions (email redacted, API tokens dropped). Set `CAPTURE = True` and walk through the two capture steps in `handle`. Restart, restate the preference, add "In test fixtures, use my email jane.doe@example.com as the sample address.", then `/events`. Then `/new-session`, `/sessions`, `/resume 1`: the whole conversation is back. Open the Agent Memory panel to show the same session in the service. Ask: do we want every old conversation in every request?
- **Recall.** Open with `/memories`; the preference has been extracted. Set `RECALL = True`; walk through the search (owner and type, not session) and how the request adds what was found. Fresh session, the de-duplication function, `/view-context`. Point out the fixture memory with `[REDACTED]` in `/memories` and the raw email still in `/events`: exclusions protect long-term memory, not the session. Say "Actually, I've switched to NumPy-style docstrings.", explain retrieval while extraction runs, then `/memories`: one docstring memory, updated. Before **Forget**, check *Extraction: up to date* (`/events`, or the session in the panel): a pending run can re-learn it. Forget it in the panel; ask again: *Recalled: nothing*. Restate Google-style for the finale.
- **Playbook.** Personal to organisational. Show `SKILL.md`, run `/publish-skill`, then `/skills`. Set `PLAYBOOK = True`; show FizzBuzz getting no team procedure and the report-rules question getting it (the `SKILL_MIN_SCORE` threshold). Then promotion: Iris console (http://localhost:18080) → Playbook → **Proposals**. Open the fixture-data proposal (everyone asked it at the end of section 4) and show its evidence. Rewrite the answer to the approved one ("No. Test fixtures must use synthetic data… Real customer data never goes into the repository, even masked."), **Accept as draft FAQ**, then publish it from **Entries**. The room asks it in their own words and sees *Team answer: …*.
- **Close (2 minutes).** All three flags on, `/new-session`, then "Show me a function that validates the rows of a report." `/view-context`: `AGENTS.md`, the recalled preference and the team procedure in one request, each with its owner.
- **Discussion.** Below.

## Discussion prompts

| Question | Point to |
| --- | --- |
| Who can read a memory? | Recall filters by owner, but isolation comes from how stores, keys and namespaces are provisioned. |
| Can we correct or delete what it learned? | Say so in conversation and extraction updates the old memory; Forget deletes one; retention expires the rest. |
| What about sensitive data? | Exclusions redact or drop matches before anything reaches long-term memory (built-in detectors, your own regex, or a plain-language rule). Session events keep the raw text until they expire, so decide what you capture at all. |
| Who decides what becomes a team answer? | Extraction only proposes. A person edits and accepts a proposal, and publishing is a separate step; until then no agent sees it. |
| Who approves a procedure? | Playbook separates creating a version from publishing it; only the publisher needs write access. |
| How do changes roll out? | Agents retrieve the current published version, and its name and version appear in the request. |
| What can we configure? | The Agent Memory panel's Store settings tab shows retention, extraction cadence, summarization and sensitive-data exclusions. |

## Before the session: the workshop Playbook

Create the workshop's own Playbook, **BofA Coding Agent Workshop**, with its skills (`skills/`) and FAQs (`faqs/faqs.json`), and a read-only key for attendees:

```bash
uv run --group iris python scripts/iris_preview_playbook.py
```

Safe to run again: a skill whose text changed gets a new version, and nothing else changes. The FAQs are labelled as workshop examples. The fixture-data FAQ is deliberately missing: you create it live through promotion in section 5.

## Before the session: Playbook promotion

Point the Playbook's FAQ extraction at the workshop store, with a one-minute idle window, so proposals appear during the session:

```bash
uv run python scripts/iris_preview_extraction.py --idle-seconds 60
```

It's idempotent. Playbook scans every 5 minutes (fixed), so a proposal appears within about 6 minutes of a session going quiet; attendees ask the fixture question at the end of section 4, well before the promotion beat. Expect noise too: extraction proposes most questions people asked (FizzBuzz, slugs). Dismiss a couple live, since that is why a person reviews, and accept the fixture one. In **Proposals**, dismiss any left over from rehearsals so the room sees a clean inbox.

## Reset the workshop state

To rehearse again from the start (flags off, `project/` as shipped, a new learner identity), press **Reset workshop** at the top of any lesson in the guide. Attendees can use it too. From a host terminal, the same reset is:

```bash
python3 scripts/prepare_workspace.py --reset . .workshop-memory
```

Your previous `agent.py`, `project/` and identity move to `.workshop-memory/.backups/`. Type `exit` in the terminal and start the agent again; no container restart is needed. As it starts, it deletes the previous learner's long-term memories and sessions from Redis Agent Memory (it prints how many), so you begin from a completely new state. Playbook proposals already drafted from those sessions stay in the Proposals inbox; dismiss them there.

## If something goes wrong

| You see | Try |
| --- | --- |
| `/memories` is empty | Extraction takes up to a minute or two. Check the preference was said after capture was switched on. |
| `/sessions` is empty | Sessions are only stored once capture is on. |
| `/skills` says there's no team skill | That workspace is missing `PLAYBOOK_SKILL_ID`. |
| `/skills` shows nothing for the task | The entry isn't published, or the ID is from another Playbook. |
