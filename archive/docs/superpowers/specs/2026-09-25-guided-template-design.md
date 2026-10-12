# Standalone guided coding-agent workshop

The user selected a standalone coding-agent workshop based on the `guided`
branch of `redislabs-training/redis-beyond-the-cache-workshop`.
Upstream revision: `c2aaf0edf7ae914e592ba60282f057e90670172e`.

## Design

Adapt `workshops/template/frontend` and its shared Vue components inside
`docker-workshop/frontend` and `docker-workshop/vendor`. Keep the upstream
Welcome / Review / Demo / Build navigation and Markdown lesson manifests.
Welcome describes this workshop; Review explains messages, schemas, tools,
approvals and verification; Demo walks through the completed loop; Build
contains the existing six exercises in order.

The Build page pairs instructions with the editor and switchable Terminal / App
Preview panes. A small typed FastAPI service implements the editor API over the
existing `docker-workshop/student` workspace. A real ttyd/tmux shell runs there
too, supporting interactive prompts, Ctrl-C and long-running capstone servers.
Nginx serves the Vue frontend and proxies `/api/`, `/terminal/` and `/app/`.
Only the frontend port is published, on localhost by default.

Existing Python exercises, blanks, solution implementations and local execution
remain intact. Retain the old workbench configuration as an explicit legacy
Compose option. The new Compose stack has its own project name and does not
stop the user's currently running terminal container. Student Python environments
live in Docker volumes to avoid reusing macOS virtual environments in Linux.

Editor requests use typed models, reject paths outside the student workspace,
hidden/generated files and symlinks, and return visible save/read errors. File
changes are saved before switching files; unsaved text is protected on navigation.
The API has no LLM calls. Live model exercises continue to use the supplied
AGENT_* environment variables inside the container.

## Validation

- API integration tests: listing, nested reads, save persistence, invalid input,
  forbidden paths and missing files.
- Frontend production build and lesson/renderer tests.
- Docker Compose validation and isolated stack startup.
- Browser smoke flow: Welcome to Build, all six steps, edit/save/reload a test
  file, run a shell command, and view a temporary FastAPI response in Preview.
- Existing deterministic checks, distinguishing the expected failures in
  intentionally incomplete student exercises from regressions.

## Alternatives considered

Importing the full hub would add unrelated workshops and deployment services;
the user chose standalone. Keeping Docsify with cosmetic changes would not
adopt the requested guided template. The selected design imports and adapts the
actual template with only the runtime integrations needed by this course.
