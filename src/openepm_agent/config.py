import os
from pathlib import Path
from dotenv import load_dotenv

# Load config file if it exists
load_dotenv("/etc/openepm-agent/config.conf")

SERVER_URL = os.getenv("OPENEPM_SERVER_URL", "http://localhost:5000")
POLL_INTERVAL = int(os.getenv("OPENEPM_POLL_INTERVAL", "5"))
REQUEST_TIMEOUT = int(os.getenv("OPENEPM_REQUEST_TIMEOUT", "10"))
BOOTSTRAP_SECRET = os.getenv("OPENEPM_BOOTSTRAP_SECRET", "")

# State file — where the agent stores its agent_id and auth_token after enrolling
CONFIG_DIR = Path("/etc/openepm-agent")
CONFIG_FILE = CONFIG_DIR / "agent.conf"