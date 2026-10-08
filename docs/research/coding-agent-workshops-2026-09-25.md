# Research: improving the coding-agent workshop

> Implementation update: the approved core redesign is now implemented. Assessments below describe the workshop before this change; validation is recorded in [VALIDATION.md](../../docker-workshop/VALIDATION.md).

Researched 25 September 2026. This is an assessment and proposed teaching changes; no workshop implementation has changed.

The strongest opportunity is to make capability growth and successful repair visible to learners. Keep the standalone Python workshop, explicit agent loop, deterministic tests, and guided browser workspace.

**Selection and evidence**

I compared public materials for workshops and closely related practical courses. Selection favored building the runtime itself, an incremental teaching sequence, inspectable exercises, and applicability to our 90-minute foundations lab. These are the three strongest matches I found, not an exhaustive ranking of everything online. Boot.dev is explicitly a self-paced guided project rather than a live workshop.

The assessment uses author-published instructions, repository materials, and individual lessons. I did not attend the sessions, watch the complete recordings, or run their projects. Recommendations about learning outcomes are judgments to validate in a pilot, not measured comparisons of teaching effectiveness.

| Reference | Fit for us | Best lesson to borrow | Adaptation constraint |
| --- | --- | --- | --- |
| Geoffrey Huntley — How to Build a Coding Agent | Closest workshop teaching sequence | Add one capability, then demonstrate what it enables | Translate the progression from Go to our existing Python stack |
| Alexey Grigorev — Build a Coding Agent with Tools, Skills and PydanticAI | Closest Python workshop | Inspect a real tool round trip; give the agent a prepared application | Keep frameworks and skills outside the introductory core |
| Boot.dev — Build an AI Agent in Python | Closest exercise and assessment model | Use an intentionally broken application as the final task | Select a few exercises from a much longer guided project |

**1. Geoffrey Huntley: capability growth learners can see**

The published workshop dates to August 2025. Its repository supplies six executable versions, progressing through chat, reading, listing, shell execution, editing, and code search. Each version comes with a task to try. The accompanying article also demonstrates a person manually supplying a requested tool result before automating execution. [Workshop article](https://ghuntley.com/agent/), [repository and progression](https://github.com/ghuntley/how-to-build-a-coding-agent).

Our adaptation: introduce a runnable one-tool checkpoint between chat and the complete agent. Ask about a prepared file before exposing tools, inspect the structured read request, manually supply its result, then automate the same interaction. Give learners a concrete success condition at every transition.

Assessment: especially useful for making the model/runtime boundary tangible. Keep our tests and approval UI; the teaching sequence does not require adopting its language, environment tooling, or historical model recommendations.

**2. Alexey Grigorev: build within a concrete application**

The April 2026 workshop starts with explicit tool calling, adds a coding toolset and on-demand instruction files, then ports the agent to PydanticAI. Its public implementation first compares questions with and without tools, inspects returned arguments and call identifiers, and eventually gives the agent a prepared Django project. The event page says no recording is available. [Workshop overview](https://aishippinglabs.com/workshops/coding-agent-v2), [public implementation guide](https://github.com/alexeygrigorev/workshops/blob/main/coding-agent-v2/README.md).

Our adaptation: provide a tiny FastAPI project with known files, a launch command, and acceptance checks. Learners should spend capstone time watching their agent investigate and change that project. Add a short prompt experiment against the same task, so instructions have an observable effect.

Assessment: strong fit for Python and our existing App Preview. Framework comparisons and skill loading make useful later exercises, but including both would crowd our 90-minute agenda.

**3. Boot.dev: prove the agent can repair a bug**

This Python guided project is listed as 20 lessons and 12 hours. It builds filesystem functions and execution before function calling and the feedback loop. Its final repair exercise deliberately changes calculator behavior, demonstrates an incorrect result, and asks the learner's agent to fix it. Public lesson text is readable; interactive features have account or membership gates. [Course overview](https://www.boot.dev/courses/build-ai-agent-python), [repair exercise](https://www.boot.dev/lessons/e457f633-6cbf-44bd-9eec-8a938f8db13a).

The execution lesson also specifies successful and failing inputs, including nonexistent files and paths outside the permitted directory. This offers concrete examples of testing a tool independently of the model. [Run Python lesson](https://www.boot.dev/lessons/c56e704c-3b4d-4673-8333-81a93a34fdd0).

Our adaptation: seed a small, reproducible FastAPI bug and require a failing check before the agent works, followed by passing checks and a working preview. Add one controlled tool error to the loop exercise.

Assessment: the strongest reference for turning completion into observable evidence. Borrow the exercise pattern and retain our short format, provider configuration, and existing test harness.

**What our current workshop already does well**

The current [workshop outline](/Users/samuelagbede/Documents/Projects/redis-coding-agent/WORKSHOP.md) specifies six stages and a 90-minute scope. It exposes messages, schemas, dispatch, feedback, termination, and verification directly.

The active [student loop tests](/Users/samuelagbede/Documents/Projects/redis-coding-agent/docker-workshop/student/tests/test_agent.py) already cover stopping, dispatch, multiple tool rounds, multiple calls, an iteration limit, and forwarding tool errors. The [rehearsal harness](/Users/samuelagbede/Documents/Projects/redis-coding-agent/docker-workshop/student/rehearse.py) independently launches generated code and checks its response. Those are valuable foundations to retain.

The main learning gaps are visible in the current lessons: [prompts and tools](/Users/samuelagbede/Documents/Projects/redis-coding-agent/docker-workshop/frontend/public/build-steps/03-prompt-and-tools.md) primarily asks learners to inspect prebuilt functionality; [agent loop](/Users/samuelagbede/Documents/Projects/redis-coding-agent/docker-workshop/frontend/public/build-steps/04-agent-loop.md) immediately shows both complete answers; [capstone](/Users/samuelagbede/Documents/Projects/redis-coding-agent/docker-workshop/frontend/public/build-steps/06-capstone.md) asks for a Hello World FastAPI application.

**Recommended changes, in order**

| Priority | Change | Learner evidence | Likely scope |
| --- | --- | --- | --- |
| 1 | Add a one-tool checkpoint and implement a small `read_file` exercise before the general loop | Learner can identify the request, arguments, execution, matching result, and next model response | Medium: checkpoint, exercise, focused tests |
| 2 | Replace the Hello World capstone with repair of a supplied FastAPI app | A supplied test fails first; the agent diagnoses and fixes the implementation; unchanged acceptance tests pass; preview works | Medium: fixture app, lesson, rehearsal update |
| 3 | Add a controlled failure/recovery exercise | A missing file or failed replacement becomes tool feedback; learner explains the subsequent action | Small: fixture, trace, lesson; extend existing tests only where needed |
| 4 | Put solutions behind a hint sequence | Learner attempts a prediction and implementation before revealing the answer, with checkpoints available for catching up | Small: lesson edits and disclosure controls |
| 5 | Offer persistent memory as a follow-on module | A preference survives process restart and can be inspected and deleted | Separate extension; outside the core 90 minutes |

For the failure exercise, use a scripted response sequence first so everyone encounters the intended error. Follow with a live attempt; do not promise that a model will choose an identical recovery path every time. Show observable messages and tool results, not purported hidden model reasoning.

For the capstone, supply a tiny task-list API with one seeded update bug and a minimal page already wired into App Preview. The required task is repair; adding a filter can be a stretch goal. Keep the acceptance checks outside the agent's editable exercise files. This combines a bounded project with independent verification.

For memory, begin with a demonstrated problem: restart the agent and lose a project preference. Then introduce Redis persistence and distinguish conversation history, stored preferences, and any later summarization. This is an original extension proposal; the three selected references do not establish Redis as necessary for the introductory loop.

**A proposed 90-minute pilot**

| Minutes | Activity |
| --- | --- |
| 0–10 | Preflight and a brief completed repair demo |
| 10–25 | First model call and message history |
| 25–40 | Implement one file tool and inspect its manual round trip |
| 40–60 | Complete dispatch, feedback, and termination; run loop tests |
| 60–70 | Controlled error, approval behavior, and recovery |
| 70–85 | Repair the prepared FastAPI app and verify independently |
| 85–90 | Explain the loop back; introduce optional extensions |

This reallocates time: provide `web_fetch` ready-made in the core and keep implementing it as an optional exercise. Do not add the new material on top of the existing schedule. The allocation is a proposal to rehearse, not a validated duration.

During the pilot, record time to each checkpoint, hint/solution usage, capstone success, and whether learners can explain who executes tools and how results reach the next model call. Keep deterministic runtime correctness separate from live task success. Update the rehearsal harness to match the revised student capstone before teaching it.

**Other candidates considered**

Hugo Bowne-Anderson and Ivan Leo's [workshop repository](https://github.com/hugobowne/build-your-own-ai-assistant) offers useful Python checkpoints and later persistence/compaction material. It is a strong follow-on reference, but its broader assistant scope makes Boot.dev a closer core exercise match. [Mastra's workshop](https://mastra.ai/workshops/build-your-own-coding-agent) is useful for framework-based tooling; our explicit-loop goal favors the selections above. [Thorsten Ball's tutorial](https://ampcode.com/notes/how-to-build-an-agent) is a useful additional introduction, but substantially overlaps the incremental tool-building lesson already represented by Huntley.

**Additional check: Vercel Academy, requested by the user**

Reviewed the course overview and eight relevant lessons on 25 September 2026. Joel Hooks's [Build Your Own AI Coding Agent Harness](https://vercel.com/academy/build-ai-agent-harness) builds TeensyCode in TypeScript using AI SDK and sandbox implementations. It extends into context management, delegation, lifecycle, and UI surfaces. It is a particularly useful reference for the runtime around the loop. Its introductory implementation uses `ToolLoopAgent`, whereas our learners implement the loop themselves. [First lesson](https://vercel.com/academy/build-ai-agent-harness/from-chat-to-agent).

The course strengthens the previous recommendations and adds a missing topic: bounded context. The following are proposed adaptations, not implemented changes.

| Learning | Concrete adaptation for our workshop | Where it fits |
| --- | --- | --- |
| Teach each capability as a response to an observed limitation | Use a recurring sequence: predict, observe the limitation, implement, verify. Give each lesson an observable completion condition | Throughout the existing lessons |
| Tool descriptions influence which action the model selects | Compare a vague `read_file` description with one explaining intended use, inputs, output, and when another tool is preferable | Existing prompts/tools segment |
| Tool output needs limits and a way to request more | Demonstrate a large file, return a bounded excerpt with an explicit truncation notice, and fetch a later range | First file-tool exercise, with supplied pagination support if needed |
| Verification claims should match recorded evidence | Require the capstone answer to identify changed files, commands run, results, and anything unverified | Capstone acceptance rubric |
| Project instructions are an explicit input to the runtime | Load a trusted fixture `AGENTS.md` containing the FastAPI project's actual test and launch commands; compare behavior with and without it | Optional exercise or supplied capstone setup |

The teaching structure is visible in the [course overview](https://vercel.com/academy/build-ai-agent-harness) and lesson outcomes, exercises, and completion checklists. The [tool-description lesson](https://vercel.com/academy/build-ai-agent-harness/descriptions-that-work) explicitly changes descriptions and tests routing. We should measure behavior on our chosen model rather than assume its exact five-section wording is universally required.

The [output-design lesson](https://vercel.com/academy/build-ai-agent-harness/tool-output-design) pairs output caps with truncation notices and pagination. Our current [student tools](/Users/samuelagbede/Documents/Projects/redis-coding-agent/docker-workshop/student/tools.py) cap `web_fetch` in the exercise contract, but `read_file`, `list_files`, and `run_bash` return unbounded results. This is the most concrete new gap. Add a small before/after demonstration using tool-result size and, where available, API-reported input tokens. Character counts must not be labeled token counts. The [context measurement lesson](https://vercel.com/academy/build-ai-agent-harness/the-problem) provides the experimental pattern; actual growth and savings depend on the task.

The [verification contract](https://vercel.com/academy/build-ai-agent-harness/verification-contract) sharpens our existing emphasis on evidence. Preserve the independent acceptance runner, and establish a baseline before calling a failure pre-existing. The [project-context lesson](https://vercel.com/academy/build-ai-agent-harness/project-context) supplies a small extension that connects generic agent behavior to project conventions without requiring a new framework.

The [approval lesson](https://vercel.com/academy/build-ai-agent-harness/approval-gates) usefully separates permission outcomes from execution outcomes. In our existing failure exercise, show both a denied tool call and an approved command that fails. Its command-prefix checks and automatic background approval are simplified examples; a matching prefix does not constrain everything a compound shell command can do. Similarly, resolving a path in the first lesson is not, by itself, a project-directory containment check. These are reasons to adapt the concepts carefully rather than treat the snippets as complete isolation mechanisms.

**Effect on the proposal:** keep the 90-minute schedule. Refine the first-tool exercise to include bounded output, use the prompt/tools slot for a description experiment, and strengthen the capstone reporting rubric. Keep `AGENTS.md` loading as an optional exercise or prebuilt setup. Context pruning, subagents, cloud lifecycle, and durable memory belong in later modules; teach the difference between limiting active context and persisting information before introducing Redis memory.
