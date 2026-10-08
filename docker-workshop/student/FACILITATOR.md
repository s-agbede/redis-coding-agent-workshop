# Facilitator guide

Guide the group from one FizzBuzz request to their own working coding agent. Use the [90-minute schedule](WORKSHOP.md), including ten minutes of buffer. The audience is experienced Python developers learning the boundaries of an LLM application.

## Prepare before the session

From `docker-workshop/`, preserve any existing `.env`, configure the model service and run `docker compose up --build -d`. Open http://localhost:8080. Each learner needs an independent stack. Browser edits apply to `docker-workshop/student/`; root files are a separate CLI starter.

If credentials are already configured in the repository root `.env`, you can instead run `docker compose --env-file .env -f docker-workshop/docker-compose.yml up --build -d` from that root. Reuse the same `--env-file` on subsequent Compose updates so the runtime keeps the intended configuration.

Run `uv run python check_setup.py` in the embedded Terminal. It checks dependencies and configuration presence without contacting the provider or printing credentials. Validate an actual model request separately using completed code in a disposable workspace. Configuration changes require `docker compose up -d --force-recreate runtime` from the host's `docker-workshop/` directory.

Distribute the exercise placeholders and intentionally broken capstone. Do not copy solutions into the learner starter when validating. Rehearse the completed agent against a fresh temporary copy of the app:

```bash
uv run python rehearse.py -n 1
```

This makes live model calls, checks the initial app, runs the supplied completed agent and independently checks the outcome. A repaired source is rejected so the rehearsal always begins with the intended bug. Saved runs under `output/rehearsal/` contain the trace, checks and file diff. Use multiple runs to investigate variation; one success is one trial.

Rehearsal uses the interactive agent's step budget: 25 by default, configured through `AGENT_MAX_ITERS`. Inspect the saved diff and final checks even when the model's report sounds convincing.

## Teach the seven lessons

1. **First call, 7m:** explain LLM, GPT model, API and Python SDK before learners implement `ask`. Run `uv run python first_call.py` against the live service. The FizzBuzz prompt already lives in the source; explain the harness after the response. A returned code block is text; no generated code has executed. End by inviting a prediction about “Now change it to stop at 20.”
2. **PEAS, 5m:** apply the four categories to the promised refresh bug. Give pairs two minutes to propose a design before revealing ours. Performance must include a later read or refresh and preserved existing behavior. Bring it back at evaluation.
3. **Conversation, 9m:** ask whether the next request contains the earlier code, then run `first_call.py --show-messages --prompt "Now change it to stop at 20."`. Inspect the actual one-message preview before explaining the gap. Learners complete `chat_turn`, start `checkpoints.stage1_chat --show-messages`, and repeat the two-turn exchange. Predict and inspect the second request's user/assistant/user order. A lucky answer does not change what was sent. Shortened previews still forward full content; this is supplied tracing, not a simulated response.
4. **First tool, 12m:** ask what evidence the chat has about the fictional local brief before submitting its release-name question. Inspect the preview. Explain schema, Python execution and tool result, then implement the plain reader and retry with `checkpoints.stage2_one_tool`. At its pause, ask which function and arguments will execute. Match the requested and returned IDs and compare the answer with the file evidence.
5. **Better reader, 7m:** read the release log with the plain reader. Have learners locate the decision and inspect the output volume. Before revealing our contract, ask what a shortened result must preserve. Compare selected text, line numbers and continuation. Learners add the helper call and retry the same question with `--paged`. Inspect actual arguments, counts and evidence; neither a model mistake nor context-window exhaustion is required. Let learners decide whether they need another page. Continuation and description experiments are outside the core time budget.
6. **Loop, 13m:** predict the observations needed to follow the brief's reference, then inspect requests without results in the one-exchange trace. Complete stopping, dispatch and feedback and immediately retry with `AGENT_VERBOSE=1 uv run python main.py`. This displays full returned file excerpts, including their bounds and continuation guidance. Spend a minute on a learner-chosen follow-up; the example distinguishes a release condition from evidence that checks passed. Allow reuse of prior observations. Then introduce supplied editing, errors and command approvals as preparation for the repair. If response latency runs beyond that minute, continue the discussion while it completes and protect the capstone's start.
7. **Repair and evaluation, 25m:** reproduce the promised bug and ask for a hypothesis before submitting the ticket. After the agent's attempt, learners inspect the changed handler and explain why a later read should now return the updated state. Run the supplied tool, harness and independent application checks, then verify refresh with a fresh task. Unit tests first appear here; explain why harness tests use prepared replies. Close by connecting the learner-built request/history/tool/feedback path to the observed repair.

Use a two-minute welcome to name the concrete repair destination, then begin building. Keep the ten-minute buffer. Invite a prediction before each comparison and reveal explanations after learners inspect the result. These questions replace recall questions; there is no extra record-keeping task or mandatory closing reflection. Hints and solutions remain available whenever useful.

If the group falls behind, omit optional reader experiments and shorten discussion. Preserve the final independent application check and browser verification. Use catch-up solutions to help learners reach that outcome without consuming the entire final task on syntax errors.

Aim to start the repair at minute 55. In the loop lesson, protect the first working run and a brief check that learners can explain who executes a requested function and how its result reaches the next model call. If needed, use the inline answers to get there. Keep the supplied-controls explanation short and point back to it when a command approval appears in the capstone.

## Running the exercises and catching up

Learners save in Code, then select **Run code** on a shell block. This reveals Terminal and submits the command to its existing shell. A successful submission is not proof that the command passed; read the output. **Copy code** is for Python answers, and **Copy text** is for prompts or protocol examples. The learner pastes a prompt into an already-running chat.

Run code needs an idle shell. If a chat is running, type `exit` before starting another command. Use Ctrl+C to interrupt a command when appropriate. Restarting a Python program loads saved edits and clears its in-memory conversation. Run code does not save an unsaved editor buffer.

All guided model exercises use the real configured service. Provide API access before teaching, and verify it privately; the learner should not need to edit `.env`. If service access fails, diagnose the actual error. Do not substitute a prepared response and present it as a live success. The deterministic clients belong inside the supplied tests, introduced during the final evaluation.

Before the conversation follow-up, learners need their completed `first_call.ask`. Before the one-tool checkpoint, they need the plain reader; the full agent needs the improved reader and loop. A test suite can help the instructor diagnose a problem, but there is no separate pytest task in lessons 1–6.

Inline answers replace just the relevant function or gap. If needed, learners can preserve their attempt and copy the corresponding completed file from `solutions/`: `first_call.py`, `stage1_chat.py`, `tools.py` or `agent.py`. Copy `stage1_chat.py` into `checkpoints/`. The full tools solution skips the plain-reader stage, so prefer the inline plain-reader answer in lesson 4.

If a provider outage blocks the final repair, a manual demonstration can still show how the app and independent checks work. State clearly that this is not a live-agent trial. The supplied `solutions/capstone_app.py` is a final catch-up option after preserving the learner's attempt.

## Troubleshooting

- **An exercise raises NotImplementedError:** confirm the named function was changed and saved. Stop and rerun the Python process to load the edit.
- **History seems stale:** restarting creates a fresh list. Repeat both prompts when comparing conversation behavior.
- **Authentication or model errors:** check host `.env` and service configuration privately. Recreate runtime after changes; do not display credentials.
- **A tool repeats or its result disappears:** inspect the assistant request, matching `tool_call_id` and the next request's messages.
- **A command is denied:** that denial is feedback. It does not mean the command executed or passed.
- **Preview is blank or reports 502:** start Uvicorn on `0.0.0.0:8000` using the lesson command. Inspect `/tmp/capstone-preview.log` if needed. Reuse an existing preview server if the port is already occupied.
- **Tasks disappear during editing:** Uvicorn reload restarted the process and cleared its in-memory store. After repair, create a fresh task, complete it and refresh without editing again.
- **The agent claims success but checks fail:** use the failed behavior as the next prompt. Keep the independent checker unchanged.

The execution tool and working-directory choice are teaching conveniences, not a production security boundary. Discuss that limit when explaining the supplied approval helper, without turning it into a separate setup lesson.

## Pilot the pacing and learner decisions

Before treating the schedule as validated, rehearse with an experienced Python developer who is new to LLM applications. Observe whether they can name the destination early, identify the missing history from the request preview, justify the bounded reader's result, choose a follow-up and explain the accepted repair. Note elapsed times and moments of lost momentum or instructor rescue. Collect this as facilitator feedback, without adding forms to the learner workflow.

A successful technical run establishes that the exercises work. It does not establish the learner's understanding or motivation, and one live repair does not establish agent reliability.
