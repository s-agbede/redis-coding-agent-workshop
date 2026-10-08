# Workbench Port Implementation Plan

> Use subagent-driven-development with bounded ownership and independent review.

**Goal:** Make the approved reference workbench the default workshop shell while preserving guided learning and student work.

**Architecture:** Static configurable workbench wraps the Vue instructions app at /guide/, code-server, and the existing shared Python runtime. All routes share localhost:8080.

**Tech Stack:** Existing JavaScript/CSS shell, Vue/TypeScript guide, Nginx, Docker Compose, code-server, Python/uv.

## 1. Coordinate and snapshot
- [x] Notify both active file-opening and panel-layout tasks; centralize deployment.
- [x] Record pinned upstream source and current source snapshot outside the workspace.
- [x] Document accepted design and ownership; no student/source exercise edits.

## 2. Workbench shell (shell agent)
Own workbench/index.html, config.js, assets/script.js, assets/style.css and workbench/tests.
- [x] Adapt pinned reference shell to Instructions=/guide/, Code=/vscode/?folder=/workspace, Terminal=/terminal/, Preview=/app/.
- [x] Add failing behavioral tests for same-origin file routing, iframe preservation and panel expand/restore including Instructions.
- [x] Keep existing frames alive when resizing, hiding and expanding; use accessible controls and resize support.
- [x] Implement safe message contract open-workshop-file with relative path; preserve legacy open-vscode-file only for local validated destinations.
- [x] Run Node tests and report exact changes/limits.

## 3. Instructions embedding (guide agent)
Own frontend/src, frontend/tests and guide-responsive styles, excluding Docker/nginx/config/prose.
- [x] Add tests for /guide embedded mode without custom CodeEditor/terminal instances.
- [x] Preserve lesson navigation, explanations, evidence keys, notes, safe renderer and source reference.
- [x] Route explicit and inline file links by same-origin parent message {type:'open-workshop-file', path:'agent.py'}.
- [x] Use /api/editor/files listing at the workbench origin; retain standalone editor behavior for legacy development.
- [x] Run frontend test and TypeScript checks.

## 4. Integration and operations (parent)
Own Compose, frontend Dockerfile/nginx/vue config as needed, code-server image/config, README/SETUP/provenance and validation.
- [x] Keep Compose name and runtime/student volume; run code-server in the same Debian runtime at /workspace, with a fresh platform-compatible virtualenv volume and persistent editor state.
- [x] Serve upstream workbench at / and compiled Vue guide at /guide/; preserve runtime API/terminal/preview routes and websocket headers.
- [x] Ensure code-server uses the runtime's Python/uv environment or clearly routes student commands to the shared Terminal; do not silently supply a broken integrated terminal.
- [x] Update operational docs and actual guide instructions to match Code panel commands and paths.
- [x] Validate Compose configuration without printing secrets, build/deploy and inspect actual browser path.

## 5. Review and verify
- [x] Review integration against spec independently, then code quality; fix findings.
- [x] Verify no code/terminal frame reload on panel toggles, all panels expand and resize, file links select Code files, and saved temporary file is shared with Terminal.
- [x] Verify lessons, map, answer disclosures, evidence persistence, summary and preview routing.
- [x] Run relevant tests and production build, preserve seeded failures, document evidence and remaining limits.
