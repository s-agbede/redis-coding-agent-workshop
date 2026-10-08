# Workshop learning redesign

Approved by the user after the before/after comparison: implement the research recommendations in the existing standalone 90-minute Python workshop.

Keep the guided Vue workbench, Python SDK loop, deterministic tests, and Docker runtime. Root sources and the browser's `docker-workshop/student` copy must agree. No framework migration, persistent memory, or multi-agent curriculum in the core.

The six build lessons become: model call and conversation; one file tool and a manual round trip; descriptions and bounded output; agent loop; errors and approvals; repair capstone. Teach predict, observe, implement, verify. Reveal hints and solutions behind accessible disclosure controls. Provide ready-made web fetching and an optional implementation challenge.

Students implement `first_call.py`, `tools.read_file`, and loop termination/dispatch/feedback in `agent.py`. Read output has numbered lines, offset/limit, a fixed maximum character budget, explicit truncation, and continuation guidance. Directory and shell output also have budgets. A no-key scripted checkpoint makes a missing-file recovery visible. A live one-tool checkpoint executes exactly one tool round trip before the general loop is complete. The description experiment compares read_file with shell access without executing an unrestricted command.

Provide a small task-list FastAPI app with a seeded bug: changing completion returns success but does not persist. Serve its prepared UI on port 8000. An independent checker outside the target application verifies create/list/update persistence, unknown IDs, and preview availability. A solution fixture proves the checker can pass; the starter proves it can fail. Rehearsal copies the fixture into a temporary project, lets the completed agent repair it, and independently verifies the result. A project argument scopes the agent's working directory and loads trusted project instructions. The capstone final report lists changed files, commands, outcomes, and unverified work.

Verification: meaningful failing tests before behavior changes; completed-solution suite; intentional starter failures limited to exercise blanks; offline checkpoint execution; frontend tests, types, build; backend regression tests; real HTTP capstone checks before/after; guided browser navigation, hint disclosure, editor save, terminal, and preview. Live model rehearsal is separate and must be reported honestly if not run.
