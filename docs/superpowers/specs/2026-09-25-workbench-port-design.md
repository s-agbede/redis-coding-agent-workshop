# Workbench port design

The user approved using the semantic-cache-routing-workshop workbench while
retaining our revised pedagogy, and explicitly requested coordination with the
other active agents. This is the accepted design, not a new approval gate.

Use the reference repository's configurable panel shell at revision
276e491d2b4dcc4b4c5a24acca85d368502cbb91 as the default entry on localhost:8080.
Instructions, Code, Terminal and App Preview are separately resizable and
expandable. Code uses code-server. Preserve iframe/session state across layout
changes and validate same-origin file-opening messages.

Retain the Vue lesson renderer and evidence records as an embedded instructions
application under /guide/. In workbench mode it renders lessons only, with no
custom editor or nested terminal. All four phases, six lessons, component map,
closed answers and independent practical/conceptual/live records remain available.
Use the existing same-origin localStorage keys so previous records survive.
File buttons and inline Python file links open the real Code panel; editor files
and Terminal share the existing student directory at /workspace.

Retain the current runtime and its Python environment, editor API and terminal;
run code-server in that same runtime container at /workspace so its integrated
terminal shares Python, uv and all running services. Use the official code-server
Debian image with managed Python 3.12. Keep the old Alpine virtualenv volume
intact and create a new Debian virtualenv volume, plus persistent editor state. The editor API can supply the
file list for inline links, but the active workbench does not use its text editor.
The frontend image serves both workbench static files and the guide. Reverse proxy
/guide/, /vscode/, /terminal/, /app/ and /api/ through the same local origin.
Do not add Redis or semantic-cache/router services to the agent workshop.

Do not overwrite student code, credentials, capstone state or solution files.
Keep the existing Compose project and student bind mount so the upgrade preserves work.
Document source provenance and optional legacy shell. No Git metadata is present;
use a temporary source snapshot for review rather than inventing commits.

Acceptance: browser path uses the new shell; VS Code reads/saves a temporary
file also observed in Terminal; lesson links select actual files; changing panel
sizes/visibility preserves editor and terminal sessions; guide progress persists;
all pedagogical features remain usable; relevant unit/integration checks and
production build pass. Validate preview routing and known seeded checker outcome
without completing the learner's capstone.
