# Facilitate the memory workshop

Use the [schedule](WORKSHOP.md) and the [presenter deck](https://claude.ai/artifact/P3PvggzgEereLL3s1BcAEa). Each section is your demo, then five minutes for the room.

## Before the session

1. **Services.** Redis Agent Memory and Redis Agent Playbook, reachable from the attendee workspaces.
2. **Publish the team skill.** On your machine, with a Playbook key that can publish and no `PLAYBOOK_SKILL_ID` set:

   ```bash
   uv run --group iris python main.py --agent solutions/steps/03-playbook.py
   ```

   Run `/publish-skill` and note the entry ID. Publishing again keeps the same ID.
3. **Attendee workspaces.** Each gets the model settings (`AGENT_API_KEY`, `AGENT_MODEL`, optional `AGENT_BASE_URL`), the three `AGENT_MEMORY_*` settings, and the Playbook settings with a read-only key plus `PLAYBOOK_SKILL_ID` set to your entry ID.
4. **Redis Insight** (panel menu → Redis Insight) is pre-connected to the Playbook's Redis. Set `PLAYBOOK_REDIS_PASSWORD` (and the host and ports, if not local) in `.env`.
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
uv run --group iris python main.py --agent solutions/steps/03-playbook.py   # run /publish-skill, note the entry ID
source scripts/use_iris_preview.sh            # attendee view: read-only app keys
export PLAYBOOK_SKILL_ID=ent_...              # the entry ID you just published
```

The workshop's current SDK versions work with the preview. Recall filters on the custom `coding_preference` memory type, so the workshop needs its own store:

- `python3 scripts/iris_preview_store.py` creates the `coding-agent-workshop` store from `agent-memory/store.json` (with that type) and a key for it; `use_iris_preview.sh` then uses it.
- The preview ships with custom extraction switched off. Set `"custom_extraction": {"enabled": True}` and add a `custom_extraction` strategy next to `instruct` under `promote_session_memory` in the preview's `scripts/local/config.py`, then `task up` again.
- On a store without the type (for example the hosted one), remove the `memory_type` filter from `recall_preferences`, or recall finds nothing.

`task down` deletes the cluster and its data.

## Running it

Your `agent.py` follows the same snapshots as the room. After each change: save, `exit`, relaunch.

- **Recap.** Model asks, Python runs the tool, the result goes back. Ask today's question.
- **The amnesiac.** "By the way, I like Google-style docstrings on my functions." Ask for the slug function; it gets the docstring. `/new-session`, ask for the word-count function, `/view-context`: the preference is gone. Then have the agent add "we target Python 3.12" to `AGENTS.md`, start a new session and ask which Python version you target.
- **Capture.** Name Redis Agent Memory. Walk through `record_event`. Switch capture on, restate the preference, `/events`. Then `/new-session`, `/sessions`, `/resume`: the whole conversation is back. Open the Agent Memory panel to show the same session in the service. Ask: do we want every old conversation in every request?
- **Recall.** Open with `/memories`; the preference has been extracted. Walk through `recall_preferences` (owner, not session) and `preference_context`. Fresh session, the de-duplication function, `/view-context`.
- **Playbook.** Personal to organisational. Show `SKILL.md`, run `/publish-skill`, walk through `skill_context`, then `/skills`. Optional: add a rule to `SKILL.md` and publish again for version 2, then `git checkout skills/` afterwards.
- **Verify.** Fresh session: "Implement validate_report in validator.py and make the tests pass." Approve the test run. `/view-context` for the three sources, then `/verify`.
- **Discussion.** Below.

## Discussion prompts

| Question | Point to |
| --- | --- |
| Who can read a memory? | Recall filters by owner, but isolation comes from how stores, keys and namespaces are provisioned. |
| Can we correct or delete what it learned? | Redis Agent Memory has update and delete operations for long-term memories and sessions. |
| What about sensitive data? | Extraction learns from what you capture, so decide what to capture. |
| Who approves a procedure? | Playbook separates creating a version from publishing it; only the publisher needs write access. |
| How do changes roll out? | Agents retrieve the current published version, and its name and version appear in the request. |
| What can we configure? | With self-hosting, the Agent Memory panel's Store settings tab shows retention, extraction cadence, summarization and sensitive-data exclusions. |

## If something goes wrong

| You see | Try |
| --- | --- |
| `/memories` is empty | Extraction takes up to a minute or two. Check the preference was said after capture was switched on. |
| `/sessions` is empty | Sessions are only stored once capture is on. |
| `/skills` says there's no team skill | That workspace is missing `PLAYBOOK_SKILL_ID`. |
| `/skills` shows nothing for the task | The entry isn't published, or the ID is from another Playbook. |
| The agent edits `validator.py` early | It was given a report-related task. Keep the early tasks unrelated to the project ("Show me a function that…"). |
