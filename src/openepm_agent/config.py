import os
import socket
from pathlib import Path

SERVER_URL = os.getenv("OPENEPM_SERVER_URL", "http://localhost:5000")
POLL_INTERVAL = int(os.getenv("OPENEPM_POLL_INTERVAL", "5"))
CONFIG_DIR = Path.home() / ".config" / "openepm-agent"
CONFIG_FILE = CONFIG_DIR / "agent.conf"


def get_hostname():
    return socket.gethostname()


def get_ip_address():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def get_os_type():
    return "linux"
