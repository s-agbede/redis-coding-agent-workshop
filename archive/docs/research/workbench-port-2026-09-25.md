# Workbench port verification — 2026-09-25

The default Docker workshop now uses the configurable workbench from
[semantic-cache-routing-workshop](https://github.com/redis-developer/semantic-cache-routing-workshop/tree/276e491d2b4dcc4b4c5a24acca85d368502cbb91).
The revised Vue lessons remain the Instructions panel at `/guide/`; the Code
panel uses native code-server. Terminal, Code and App Preview share `/workspace`
and the same Python environment. The existing Compose project and student bind
mount were retained. The previous Alpine environment volume was retained, with
a separate Debian-compatible virtualenv and persistent editor-state volume.

## Coordination and retained teaching structure

The file-opening and expandable-panel tasks were contacted before integration
and asked to stop overlapping deployment. Their completed changes were retained
in the standalone frontend, and equivalent native file opening and panel controls
were added to the new default shell. The component map, completed offline demo,
six lessons, optional hints/answers, independent practice and separate practical,
concept and live-attempt records remain available. Student exercise implementations
and the seeded capstone bug were not replaced with solutions.

## Verification

- Final Docker build: 68 frontend tests, strict TypeScript, production Vue build,
  and 15 workbench tests passed. Both final services started; runtime is healthy.
- 67 backend tests passed. In the new Linux runtime, 71 Python tests passed in an
  isolated completed copy. The capstone remained 8/9 on the seed and became 9/9
  only in a temporary repaired copy.
- Browser walkthrough verified Welcome → component overview → three demo steps
  → six lessons and progress summary. Answers start closed. Evidence survived
  lesson navigation; demo position survived reload. Temporary evidence was cleared.
- Instructions, Code, Terminal and App Preview expand and restore. Keyboard
  resizing works. Shell regressions also cover pointer resizing, cancellation,
  hide/show, and preservation of iframe nodes during layout changes.
- A disposable file saved through Code was visible in the host bind mount and
  Terminal. A separate unsaved marker remained absent from disk and survived
  expansion, full page reload, runtime recreation and native file navigation.
  The disposable file and its test buffer were cleaned up afterward.
- Nested file links selected `capstone/index.html`. Switching to another editor
  and clicking that same lesson link selected the requested file again. The
  installed code-server version uses a native `openFile` payload; the initial
  `goto` query alone did not work and was corrected following browser verification.
- App Preview displayed its startup instructions before the server was available,
  then loaded the task board after the documented Terminal command and refresh.
- The guide's Home links return to `/guide/`, avoiding a nested workbench.
- Independent specification and quality reviews completed. All material findings
  were fixed and the final shell tests were independently rerun.

## Limits

File links navigate the Code iframe and use native hot-exit recovery; layout
changes do not navigate it. The code-server image is pinned, so its URL contract
should be browser-checked when upgrading. Existing user editor settings are
preserved; new profiles hide the unrelated AI chat interface by default.

No paid model calls or novice participant sessions were performed. The learner
pilot and provisional timing described in the pedagogical review still apply.
Existing dependency and bundle-size build warnings remain. The shell is served
on loopback by default; deployment beyond the local workshop was not undertaken.
