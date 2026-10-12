# Workbench source

The default shell is adapted from:

- Repository: https://github.com/redis-developer/semantic-cache-routing-workshop
- Commit: `276e491d2b4dcc4b4c5a24acca85d368502cbb91`
- Retrieved: 2026-09-25
- Source files: `workbench/index.html`, `workbench/config.js`,
  `workbench/assets/script.js`, `workbench/assets/style.css`.

Redis logos and existing source attribution remain. Local adaptations configure
Instructions, Code, Terminal and App Preview for coding-agent lessons, preserve
iframe state through layout changes, expand Instructions as well as other panels,
and validate source/origin/path before opening lesson files in Code.

Instructions embed the existing guided Vue application at `/guide/`; we retain
its six-lesson learning sequence, diagrams and answer disclosures.
Code uses code-server; the alternate custom editor and retired Review/Demo views
have been removed. The
runtime combines official code-server 4.127.0 (image digest pinned in its Dockerfile),
managed Python 3.12, the existing FastAPI file API and ttyd 1.7.7 (official release,
checksum-verified). No semantic-cache/router application services are copied.

The code-server runtime uses a new Debian virtualenv volume; the old Alpine
volume is retained during upgrades. Learner files are generated from the maintained root source into `.workshop/` and
bind-mounted at `/workspace`; existing learner edits are preserved on startup.

# Guided lesson source

This standalone workshop is adapted from:

- Repository: https://github.com/redislabs-training/redis-beyond-the-cache-workshop
- Branch: `guided`
- Commit: `c2aaf0edf7ae914e592ba60282f057e90670172e`
- Retrieved: 2026-09-25

`frontend/` started as `workshops/template/frontend/` at that revision.
`vendor/workshop-front-end-components/` retains the shared header and Markdown
renderer used by the guided frontend; unused components have been removed.
The upstream README and package metadata identify the project as MIT licensed;
the source snapshot did not include a separate LICENSE file. Redis attribution
and package metadata are retained here.

Local adaptations:

- Welcome and Workshop navigation, with six lessons that build one `agent.py`.
- A Python runtime with a generated learner workspace and a typed FastAPI file API.
- VS Code for editing and a real ttyd/tmux shell for running the agent.
- A managed task-board preview that starts automatically and switches to a
  separate app copy during the instructor's interactive demo.
- Production Docker images and same-origin proxy routes for the workshop stack.
- TypeScript for lesson navigation and command controls; retained upstream
  JavaScript for shared rendering and the workbench shell.
- The shared header says Workshop Home because this deployment has no hub.
- Markdown rendering preserves fenced Python code and indentation; safe native
  details/summary disclosures keep hints and solutions closed initially.
- Lessons trace a tool call, explore output limits and recovery, and end with
  repair and independent checks of a supplied task board.

The repository root is the maintained source for both local CLI use and the
browser learner workspace. The Vue application is the Instructions panel in the
default workbench. Historical designs and research are preserved in `archive/`.
