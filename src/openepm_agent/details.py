import requests
import socket
import platform
import uuid
import json
from pathlib import Path

SERVER_URL = "http://127.0.0.1:5000"
BOOTSTRAP_SECRET = "my-bootstrap-secret"
STATE_FILE = Path("agent_state.json")

def get_hostname():
    return socket.gethostname()

def get_os_info():
    return platform.platform()

def get_mac_address():
    mac_num = uuid.getnode()
    return ":".join(f"{(mac_num >> shift) & 0xff:02X}" for shift in range(40, -1, -8))

def save_state(agent_id, auth_token):
    STATE_FILE.write_text(json.dumps({
        "agent_id": agent_id,
        "auth_token": auth_token
    }))

def enroll():
    payload = {
        "hostname": get_hostname(),
        "mac_address": get_mac_address(),
        "os_info": get_os_info(),
        "bootstrap_secret": BOOTSTRAP_SECRET
    }

    response = requests.post(f"{SERVER_URL}/agents/register", json=payload, timeout=10)

    if response.status_code == 201:
        data = response.json()
        save_state(data["agent_id"], data["auth_token"])
        print("Enrollment successful.")
        print("Agent ID:", data["agent_id"])
    else:
        print("Enrollment failed:", response.status_code, response.text)