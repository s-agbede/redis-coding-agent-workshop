# Point this shell's workshop at a local Iris on-prem preview instead of the hosted services.
#
#   source scripts/use_iris_preview.sh            # attendee view: read-only app keys
#   source scripts/use_iris_preview.sh publish    # instructor: Playbook operator token, for /publish-skill
#
# Values come from the preview's .demo/local/connections.json; nothing is printed.
PREVIEW="${IRIS_PREVIEW_DIR:-$HOME/Documents/Projects/iris-onprem-preview}"
CONNECTIONS="$PREVIEW/.demo/local/connections.json"
if [ ! -f "$CONNECTIONS" ]; then
  echo "No preview connections at $CONNECTIONS. Run 'task up' in the preview first." >&2
  return 1 2>/dev/null || exit 1
fi
_iris() { python3 -c "import json; print(json.load(open('$CONNECTIONS'))['products']['$1']['$2'])"; }
export AGENT_MEMORY_URL="$(_iris memory url)" AGENT_MEMORY_STORE_ID="$(_iris memory resource_id)"
export AGENT_MEMORY_API_KEY="$(_iris memory api_key)"
# The workshop's own store (with the coding_preference type), from scripts/iris_preview_store.py.
WORKSHOP_MEMORY="$PREVIEW/.demo/local/workshop-memory.json"
if [ -f "$WORKSHOP_MEMORY" ]; then
  export AGENT_MEMORY_STORE_ID="$(python3 -c "import json; print(json.load(open('$WORKSHOP_MEMORY'))['store_id'])")"
  export AGENT_MEMORY_API_KEY="$(python3 -c "import json; print(json.load(open('$WORKSHOP_MEMORY'))['api_key'])")"
fi
export PLAYBOOK_DATA_PLANE_URL="$(_iris playbook url)" PLAYBOOK_PLAYBOOK_ID="$(_iris playbook resource_id)"
export PLAYBOOK_API_KEY="$(_iris playbook api_key)"
if [ "${1:-}" = "publish" ]; then
  # Publishing needs an operator credential; app keys can only read.
  (cd "$PREVIEW" && task token PRODUCT=playbook >/dev/null)
  export PLAYBOOK_API_KEY="$(cat "$PREVIEW/.demo/local/operator.jwt")"
  unset PLAYBOOK_SKILL_ID
fi
unset -f _iris
echo "Workshop now uses the Iris preview at $AGENT_MEMORY_URL and $PLAYBOOK_DATA_PLANE_URL."
