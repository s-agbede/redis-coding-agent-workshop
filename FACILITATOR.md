# Facilitate the memory workshop

Use the [schedule](WORKSHOP.md) and the [presenter deck](https://claude.ai/artifact/P3PvggzgEereLL3s1BcAEa). Each section is your demo, then a few minutes for the room: about an hour of content. Each lesson in the browser guide also shows its section's slides, with **Focus mode** for presenting. After changing the deck, run `python3 scripts/render_slides.py` and `uv run python scripts/publish_docs.py`.

## Before the session

1. **Services.** Redis Agent Memory and Redis Agent Playbook, reachable from the attendee workspaces. Verify the custom `coding_preference` type and enabled extraction prompt from `agent-memory/store.json`; the application filters on this exact type. Managed services do not load this file automatically. Check the actual retention and exclusion settings before presenting them.
2. **Publish the team skill.** On your machine, with a Playbook key that can publish and no `PLAYBOOK_SKILL_ID` set:

   ```bash
   uv run --group iris python main.py
   ```

   Run `/publish-skill` and note the entry ID. Publishing again keeps the same ID only when using the same local publication receipt and Playbook. If the skills are already published, skip this step: `/skills` lists the serving inventory without needing a selected skill ID. Do not create a second report-validation entry from a fresh publisher workspace.
3. **Attendee workspaces.** Each gets the model settings (`AGENT_API_KEY`, `AGENT_MODEL`, optional `AGENT_BASE_URL`), the three `AGENT_MEMORY_*` settings, and the shared Playbook settings with a read-only key. `PLAYBOOK_SKILL_ID` is optional for listing and retrieval. Keep publishing credentials in the instructor's environment. Leave `IRIS_OWNER_ID` unset in the lab template and give each lab a fresh workspace; do not copy a rehearsal's `output/workshop/owner.json`. Owner filters separate the workshop experience, not access permissions; use synthetic data. Attendees do not need Redis Cloud dashboard access.
4. **Redis Insight** (panel menu → Redis Insight) shows the Iris preview's databases when you start the workbench with `bash scripts/workbench_with_iris_preview.sh`. For other Redis databases, set `INSIGHT_DB1_*` / `INSIGHT_DB2_*` (host, port, alias, password) in `.env`.
5. **Legacy self-hosting recipe (not compatible with the current GA SDK).** Keep `docker-compose.selfhost.yml` disabled for this revision. It describes Memory 0.7 and requires a service migration before use. The current workshop uses managed GA services.
6. **Rehearse** with real services, ideally with a few people on the same memory store.

## Legacy Memory and Playbook preview (requires migration)

The current workshop pins the GA 1.1 SDKs. The older Preview and standalone Memory 0.7 routes are incompatible with these SDKs. The commands in this section are historical reference; migrate the services and rehearse before using them with this revision.

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

Recall filters on the custom `coding_preference` memory type, so the workshop needs a store configured with that type:

- `python3 scripts/iris_preview_store.py` creates the `coding-agent-workshop` store from `agent-memory/store.json` (with that type) and a key for it; `use_iris_preview.sh` then uses it.
- The preview ships with custom extraction switched off. Set `"custom_extraction": {"enabled": True}` and add a `custom_extraction` strategy next to `instruct` under `promote_session_memory` in the preview's `scripts/local/config.py`, then `task up` again.
- On a managed store, define and enable `coding_preference` in the Cloud console before the workshop. Keep the owner and type filters: removing the type filter can recall assistant-generated facts as personal preferences.

`task down` deletes the cluster and its data.

## Managed-service rehearsal prerequisites

The current local workshop uses managed services. The Memory panel browses sessions and memories and shows a dated, read-only **Store settings** snapshot for the configured workshop store. The instructor verifies or edits live settings in Redis Cloud; attendees inspect the snapshot without dashboard access.

When upgrading an existing browser workspace from the older SDK, startup preserves the learner's `agent.py` while updating dependencies. In its Section 4 search request, change `"text": task` to `"query": task`, preserving the other learner edits. SDK 1.1 ignores the old `text` field, which otherwise makes recall filter-only. Fresh workspaces already have the corrected field.

- The dedicated GA `coding-agent-workshop` store on `sam-test-db` retains sessions for one day and long-term memories for seven days, with a 60-second extraction cadence. The old Preview store is preserved.
- The GA store enables email redaction and the custom API-token drop detector from `agent-memory/store.json`. Email redaction was verified with a new synthetic session; raw session events still retain the email. Existing memories are not retroactively redacted. Use synthetic data throughout.
- Three skills and five FAQs are published: the four repository FAQs plus the customer-fixture FAQ promoted from the GA rehearsal. Use the public-AI-tools FAQ and its paraphrase for the required attendee exercise.
- Automatic FAQ extraction is enabled on the managed Playbook, using only the dedicated GA workshop store and a one-minute inactivity window. Promotion is an optional instructor demo requiring an extraction job, access to the source Memory store, and a rehearsed proposal. The customer-fixture proposal was extracted, edited, accepted as an unpublished draft, and published as v1; a paraphrase retrieves it. Its source session and event IDs appear under **Candidate source & metadata**, even when **Supporting evidence** shows zero. For a repeat live promotion, use a new question; the customer-fixture FAQ is already published. Do not enable it on a shared store without reviewing which conversations it can read. Do not claim the customer-data FAQ exists until it has been reviewed and published. The Cloud console calls the entry list **Registry**; the on-prem preview calls it **Entries**.

## Running it

Your `agent.py` follows the same flags as the room: each section switches one on in `handle`'s file. After each change: save, `exit`, relaunch.

- **Recap.** Model asks, Python runs the tool, the result goes back. Ask today's question.
- **The amnesiac.** "By the way, I like Google-style docstrings on my functions." Ask for the slug function; it gets the docstring. `/new-session`, ask for the same slug function, `/view-context`: the preference is gone. Have the agent add it to `AGENTS.md`, start a new session, and ask again: the rule appears in the request; verify the output rather than promising a deterministic model response. Then walk through what that costs (manual, applies to everyone, only grows, never expires) and name the three jobs: extraction, lifecycle, retrieval. Have the agent take the line back out.
- **Capture.** Name Redis Agent Memory. Open Agent Memory → Store settings. The managed workshop shows a dated, read-only snapshot; use the Redis Cloud dashboard link to verify or edit current settings. Show: retention, extraction, the `coding_preference` prompt, and the configured exclusions. Only promise email redaction and API-token dropping when those detectors are enabled and tested. Set `CAPTURE = True` and walk through the two capture steps in `handle`. Restart, restate the preference, add "In test fixtures, use my email jane.doe@example.com as the sample address.", then `/events`. Then `/new-session`, `/sessions`, `/resume 1`: the whole conversation is back. Open the Agent Memory panel to show the same session in the service. Ask: do we want every old conversation in every request?
- **Recall.** Open with `/memories`; the preference has been extracted. Set `RECALL = True`; walk through the search (owner and type, not session) and how the request adds what was found. Fresh session, the de-duplication function, `/view-context`. Compare the fixture memory with the configured exclusions; with an enabled email detector it should be redacted. The Sessions panel retains the full raw email; `/events` prints previews. Exclusions apply to long-term memory, not the session. Say "Actually, I've switched to NumPy-style docstrings.", explain retrieval while extraction runs, then `/memories`: one `coding_preference` for docstrings, updated. Before **Forget**, stop sending messages and wait until `/memories` shows the correction: a pending run can re-learn it. GA does not expose the older per-session extraction bookmark. Forget its `coding_preference` in the panel, start a new session, and ask again: the deleted preference should be absent. Other coding preferences may still be recalled; the old conversation would otherwise still contain the correction. Restate Google-style for the finale.
- **Playbook.** Personal to organisational. Show `SKILL.md`, then `/skills`. If demonstrating publishing, use the instructor's separate publishing environment and existing publication receipt; attendee workspaces stay read-only. Set `PLAYBOOK = True`; show FizzBuzz getting no team procedure and the report-rules question getting it (the `SKILL_MIN_SCORE` threshold). Use the prepublished public-AI-tools FAQ for the core exercise. Optional promotion, only after configuring and rehearsing it: Redis Cloud → Iris → Agent Playbooks → your Playbook → **Proposals**. Open a rehearsed proposal and inspect its source sessions and events; do not promise a nonzero supporting-evidence count. Rewrite its answer to the approved wording, accept it as an unpublished draft, then publish from **Registry**. The room asks it in their own words and sees *Team answer: …*. The customer-fixture FAQ is already published in the managed rehearsal, so use a new question for a fresh promotion demo.
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
| What can we configure? | Attendees inspect the dated snapshot in the panel. Only the instructor or store administrator edits current settings in the Redis Cloud dashboard; attendees do not have dashboard access. |

## Before the session: the workshop Playbook

Use the existing managed workshop Playbook and verify its published skills and FAQs before the session. In Redis Cloud, the instructor manages content under **Registry** and credentials under **Iris → Access & Identity**. Attendee keys need only `read`; keep content authoring and publishing permissions on the instructor's separate key. The repository's `skills/` and `faqs/faqs.json` contain the starter content, labelled as workshop examples. The managed rehearsal also contains the published customer-fixture FAQ.

`scripts/iris_preview_playbook.py` provisions the legacy local preview. It is not a managed Cloud provisioning command and must not be used for the current deployment without migrating its service calls.

## Before the optional on-prem promotion demo

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
| `/skills` is empty | Check the configured Playbook ID, read access, and whether skills are published. `PLAYBOOK_SKILL_ID` is not required to list or retrieve them. |
| `/skills` shows nothing for the task | The entry isn't published, or the ID is from another Playbook. |

### Maintaining the managed settings snapshot

`agent-memory/managed-settings.json` contains the non-secret settings verified in Redis Cloud on the recorded date. The inspector displays it only when both the configured endpoint and store ID match. It is read-only even when `INSPECTOR_ALLOW_EDITS` is enabled. After changing the Cloud configuration, verify the values, update the snapshot and its `verifiedOn` date, and rebuild the runtime image. For another store, verify its configuration before replacing the snapshot; never relabel the template as a live configuration. Self-hosted deployments with a configured Control Plane continue to read settings live.
