#!/bin/bash

# This script is used when developing on macOS.
# It starts the podman service inside of the podman machine,
# and it exposes the service on http://localhost:8080 on the host.

set -e

# Configuration
VM_NAME="podman-machine-default"
TUNNEL_PORT=8080

echo "🔍 Inspecting Podman machine..."
INSPECT_JSON=$(podman machine inspect "$VM_NAME")

IDENTITY_PATH=$(echo "$INSPECT_JSON" | jq -r '.[0].SSHConfig.IdentityPath')
SSH_PORT=$(echo "$INSPECT_JSON" | jq -r '.[0].SSHConfig.Port')
SSH_USER=$(echo "$INSPECT_JSON" | jq -r '.[0].SSHConfig.RemoteUsername')

# Sanity checks
if [[ "$IDENTITY_PATH" == "null" || -z "$IDENTITY_PATH" ]]; then
  echo "❌ Could not determine IdentityPath."
  exit 1
fi

if [[ "$SSH_PORT" == "null" || -z "$SSH_PORT" ]]; then
  echo "❌ Could not determine SSH port."
  exit 1
fi

if [[ "$SSH_USER" == "null" || -z "$SSH_USER" ]]; then
  echo "❌ Could not determine SSH username."
  exit 1
fi

echo "🧠 Identity file: $IDENTITY_PATH"
echo "🧠 SSH port: $SSH_PORT"
echo "🧠 SSH user: $SSH_USER"

# Start Podman REST API if not already running
echo "📡 Starting Podman REST API inside the VM (and verifying)..."
podman machine ssh "$VM_NAME" <<EOF
  if ! pgrep -f 'podman system service' > /dev/null; then
    nohup podman system service --time=0 tcp:0.0.0.0:${TUNNEL_PORT} > /dev/null 2>&1 &
    sleep 1
  fi
  if ! pgrep -f 'podman system service' > /dev/null; then
    echo "❌ Podman REST API failed to start inside the VM." >&2
    exit 1
  fi
EOF

echo "🧪 Verifying API availability..."
if curl -s http://localhost:${TUNNEL_PORT}/_ping | grep -q OK; then
  echo "♻️ Old tunnel still active? Cleaning up..."
  kill $(lsof -ti tcp:${TUNNEL_PORT}) 2>/dev/null || true
  sleep 1
fi

# Trap cleanup when the user exits
cleanup() {
  echo ""
  echo "🧹 Cleaning up..."

  echo "🛑 Killing SSH tunnel..."
  kill $TUNNEL_PID 2>/dev/null || true

  echo "🛑 Killing Podman REST API inside VM..."
  podman machine ssh "$VM_NAME" 'pkill -f "podman system service"' 2>/dev/null || true

  echo "✅ All cleaned up. Bye!"
  exit 0
}
trap cleanup INT TERM EXIT

# Start SSH tunnel and keep it blocking
echo "🔌 Starting SSH tunnel on localhost:${TUNNEL_PORT}..."
ssh -qNL ${TUNNEL_PORT}:localhost:${TUNNEL_PORT} \
  -i "$IDENTITY_PATH" \
  -p "$SSH_PORT" \
  "${SSH_USER}@127.0.0.1" &
TUNNEL_PID=$!

# Wait until tunnel is killed or Ctrl+C
wait $TUNNEL_PID
