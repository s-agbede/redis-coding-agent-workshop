#!/usr/bin/env bash
# Start the browser workbench (http://localhost:8080) against a local Iris on-prem preview,
# as an attendee: read-only Playbook key, the instructor's published skill, the workshop store.
# .env is left untouched; these shell values take priority over it.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
source scripts/use_iris_preview.sh

receipt=$(ls output/iris-preview/publication.json output/workshop/publication.json 2>/dev/null | head -1 || true)
if [ -z "$receipt" ]; then
  echo "Publish the team skill to the preview first (FACILITATOR.md, 'Running Memory and Playbook yourself')." >&2
  exit 1
fi
export PLAYBOOK_SKILL_ID="$(python3 -c "import json; print(json.load(open('$receipt'))['entry_id'])")"

# Containers reach the Mac's 127.0.0.1 through host.docker.internal.
export AGENT_MEMORY_URL="${AGENT_MEMORY_URL/127.0.0.1/host.docker.internal}"
export WORKSHOP_PLAYBOOK_DATA_PLANE_URL="${PLAYBOOK_DATA_PLANE_URL/127.0.0.1/host.docker.internal}"

# Lets the Agent Memory panel show the store settings. A local operator token: fine on your own machine.
(cd "$PREVIEW" && task token PRODUCT=memory >/dev/null)
export AGENT_MEMORY_CONTROL_PLANE_URL="http://host.docker.internal:19100"
export AGENT_MEMORY_ADMIN_TOKEN="$(cat "$PREVIEW/.demo/local/operator.jwt")"
# Your machine, your store: allow editing its settings from the panel. Set to 0 for an attendee view.
export INSPECTOR_ALLOW_EDITS="${INSPECTOR_ALLOW_EDITS:-1}"

# Redis Insight: expose the preview's Redis databases on this Mac and hand Insight their passwords.
KUBECONFIG_FILE="$PREVIEW/.demo/local/workbench-kubeconfig"
kind get kubeconfig --name iris-local > "$KUBECONFIG_FILE" && chmod 600 "$KUBECONFIG_FILE"
redis_password() {
  kubectl --kubeconfig "$KUBECONFIG_FILE" -n iris get secret "redis-$1-config" -o jsonpath='{.data.redis\.conf}' \
    | base64 -d | awk '$1 == "requirepass" {print $2}'
}
pkill -f "port-forward -n iris svc/redis-" 2>/dev/null || true
for pair in metadata:16480 content:16481 jobs:16482; do
  nohup kubectl --kubeconfig "$KUBECONFIG_FILE" port-forward -n iris "svc/redis-${pair%%:*}" "${pair##*:}:6379" \
    > "$PREVIEW/.demo/local/port-forward-${pair%%:*}.log" 2>&1 &
done
export INSIGHT_DB1_PASSWORD="$(redis_password metadata)" INSIGHT_DB2_PASSWORD="$(redis_password content)"

exec bash start.sh
