#!/usr/bin/env bash
set -euo pipefail

APP_NAME="openepm-agent"
APP_DIR="/opt/openepm-agent"
SERVICE_FILE="/etc/systemd/system/${APP_NAME}.service"
PYTHON_BIN="python3"
REPO_SRC="$(pwd)"

if [[ "${EUID}" -ne 0 ]]; then
  echo "Please run this script as root (e.g. sudo ./deploy.sh)"
  exit 1
fi

for cmd in rsync ${PYTHON_BIN} systemctl; do
  command -v "$cmd" >/dev/null 2>&1 || {
    echo "Missing required command: $cmd"
    exit 1
  }
done

echo "==> Deploying ${APP_NAME} from ${REPO_SRC} to ${APP_DIR}"

echo "==> Stopping existing service if present"
systemctl stop "${APP_NAME}" 2>/dev/null || true

mkdir -p "${APP_DIR}"

echo "==> Syncing project files"
rsync -a --delete \
  --exclude '.git' \
  --exclude '.idea' \
  --exclude '__pycache__' \
  --exclude '.pytest_cache' \
  --exclude '.mypy_cache' \
  --exclude '.ruff_cache' \
  --exclude 'tests' \
  --exclude 'build' \
  --exclude 'dist' \
  --exclude '*.pyc' \
  --exclude '*.pyo' \
  --exclude '.DS_Store' \
  "${REPO_SRC}/" "${APP_DIR}/"

chown -R root:root "${APP_DIR}"
chmod -R u=rwX,go=rX "${APP_DIR}"

if [[ ! -f "${APP_DIR}/pyproject.toml" ]]; then
  echo "ERROR: ${APP_DIR}/pyproject.toml not found after sync"
  exit 1
fi

echo "==> Creating/updating virtual environment"
"${PYTHON_BIN}" -m venv "${APP_DIR}/.venv"
"${APP_DIR}/.venv/bin/pip" install --upgrade pip wheel setuptools
"${APP_DIR}/.venv/bin/pip" install -e "${APP_DIR}"

echo "==> Writing systemd unit"
cat > "${SERVICE_FILE}" <<EOF_SERVICE
[Unit]
Description=OpenEPM Agent
After=network.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=${APP_DIR}
Environment="PATH=${APP_DIR}/.venv/bin"
ExecStart=${APP_DIR}/.venv/bin/python -m openepm_agent.cli start
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF_SERVICE

echo "==> Reloading systemd"
systemctl daemon-reload
systemctl enable "${APP_NAME}.service"

echo "==> Starting agent service"
systemctl restart "${APP_NAME}.service"

echo "==> Checking agent service"
systemctl --no-pager --full status "${APP_NAME}.service" || true

echo "==> Done"
echo "Service status: systemctl status ${APP_NAME}"
echo "Service logs:   journalctl -u ${APP_NAME} -e"
