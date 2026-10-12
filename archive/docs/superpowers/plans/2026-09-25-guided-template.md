# Guided Template Migration Implementation Plan

> Execute independent frontend and runtime work with the subagent-driven-development skill, then review and validate their integration.

**Goal:** Run the existing coding-agent course as a standalone instance of the supplied guided workshop template.

**Architecture:** Vue frontend and shared components adapted from the pinned upstream revision; a FastAPI editor and ttyd shell share the student workspace; Nginx proxies API, terminal and preview. Preserve student source and provide the old workbench as a legacy option.

**Tech Stack:** Existing Python/uv/FastAPI, upstream Vue 3/Vue CLI, Docker Compose, Nginx, ttyd, tmux.

- [x] Write failing editor API integration tests, then implement typed read/list/save endpoints in `docker-workshop/backend/`. Test real temporary files with FastAPI TestClient, including nested paths, missing files, validation, traversal and symlinks. Run `uv run --project docker-workshop/backend pytest docker-workshop/backend/tests -q`.
- [x] Copy the pinned template frontend and shared package into `docker-workshop/frontend/` and `docker-workshop/vendor/`; record provenance and all local adaptations in `docker-workshop/UPSTREAM.md`.
- [x] Port six Markdown exercises into the upstream build manifest, replace VS Code links with editor navigation, configure Python-only content, and adapt Demo/Review/Welcome text.
- [x] Connect the editor to the API, handle explicit saves and failures, preserve edits during file/navigation changes, and add persistent terminal and preview panes. Verify rendering and course-manifest behavior with frontend tests.
- [x] Preserve existing Compose as `docker-workshop/docker-compose.legacy.yml`; replace the default with the guided frontend/runtime services, scoped project name, localhost port and Linux environment volume. Add Dockerfiles, Nginx routing, startup scripts and dependency locks.
- [x] Run production build, API tests and Compose checks. Build and launch under a distinct project name/port; verify navigation, editor persistence, interactive terminal and preview in the browser without paid model calls.
- [x] Update root/workshop READMEs and facilitator run instructions with startup, verification, editable source, expected student failures, provenance and legacy fallback. Record final checks and any concrete limitations.

There is no `.git` directory in this workspace; commits and Git worktrees are not applicable. This is a file migration, not a history rewrite.
