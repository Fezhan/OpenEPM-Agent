#!/usr/bin/env python
import os
from pathlib import Path
from dotenv import load_dotenv

# Try system path first, then fall back to a local .env for development
_system_config = Path("/etc/openepm-agent/config.conf")
_local_config  = Path(__file__).resolve().parents[1] / ".env"

if _system_config.exists():
    load_dotenv(str(_system_config))
elif _local_config.exists():
    load_dotenv(str(_local_config))

SERVER_URL            = os.getenv("OPENEPM_SERVER_URL")
POLL_INTERVAL         = int(os.getenv("OPENEPM_POLL_INTERVAL",     "5"))
REQUEST_TIMEOUT       = int(os.getenv("OPENEPM_REQUEST_TIMEOUT",   "10"))
BOOTSTRAP_SECRET      = os.getenv("OPENEPM_BOOTSTRAP_SECRET",      "")
ENROLL_RETRY_INTERVAL = int(os.getenv("ENROLL_RETRY_INTERVAL",     "60"))

CONFIG_DIR  = Path("/etc/openepm-agent")
CONFIG_FILE = CONFIG_DIR / "agent.conf"