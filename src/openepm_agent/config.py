import os
from pathlib import Path

SERVER_URL = os.getenv("OPENEPM_SERVER_URL", "http://localhost:5000")
POLL_INTERVAL = int(os.getenv("OPENEPM_POLL_INTERVAL", "5"))
CONFIG_DIR = Path.home() / ".config" / "openepm-agent"
CONFIG_FILE = CONFIG_DIR / "agent.conf"
BOOTSTRAP_SECRET = os.getenv("OPENEPM_BOOTSTRAP_SECRET", "my-bootstrap-secret")
REQUEST_TIMEOUT = int(os.getenv("OPENEPM_REQUEST_TIMEOUT", "10"))

