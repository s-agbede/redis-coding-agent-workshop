# Repository cleanup implementation plan

**Goal:** Give the current workshop one deployment configuration and clear startup commands; remove the superseded scaffolding identified in the review.

**Architecture:** Keep the existing two-service workshop and its project name, mounts, ports and volumes. Move its Compose configuration to the root, with paths adjusted to the same physical directories. Keep nested startup wrappers for compatibility. Retain separate CLI starters and browser student files because they are independent editable workspaces.

**Tech stack:** Docker Compose, Bash, existing Vue/Python runtime.

- [x] Validate the existing Compose services and mount paths as a comparison baseline, without displaying interpolated credentials.
- [x] Move the active Compose configuration to the root; add root start/build scripts and delegate nested wrappers. Startup uses root .env when present, with the existing workshop .env as fallback.
- [x] Move tmux.conf to docker/guided and update its Dockerfile. Remove legacy Compose, Docker/web startup, unused code/web, obsolete setup documentation, and old AMS demo/CLI/requirements files. Back up local untracked demo files outside the repository first.
- [x] Update current setup/facilitator documentation and explain directory ownership. Preserve the separately requested install-requirements.sh and explain that it is optional, not the workshop deployment path.
- [x] Compare resolved service paths/project identity; validate shell syntax, exercise root/nested commands with a harmless Docker stub, run lesson progression/frontend checks, and build the runtime image to verify moved build inputs. Do not restart the active learner session or delete Docker volumes.

## Verification results

- Resolved Compose project, service build contexts, mount paths, published port and named volume declarations match the pre-cleanup deployment.
- Eight script routing checks passed, covering root/nested invocation, invocation from another directory, argument forwarding, and root/legacy/no env-file selection.
- Shell syntax and `git diff --check` passed.
- Ten documentation/progression checks passed.
- Both Docker images built successfully. The frontend build ran 80 frontend tests, strict TypeScript checking, production compilation and 16 workbench tests successfully.
- Existing containers remained running, runtime healthy, and the workshop returned HTTP 200. No learner-session restart or volume deletion was performed.
- Removed the unused nested image-builder workflow targeting a separate upstream infrastructure repository.
- The separate AMS demo, including its ignored local environment files, was preserved at `/private/tmp/workshop-legacy-backup-wyu9i1np/ams-preferences-app` before removal. Tracked historical content also remains in Git history.
