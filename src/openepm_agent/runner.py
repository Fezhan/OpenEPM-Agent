import json
import time

import requests

from .config import CONFIG_DIR, CONFIG_FILE, POLL_INTERVAL, BOOTSTRAP_SECRET, SERVER_URL, REQUEST_TIMEOUT
from .details import get_hostname, get_mac_address, get_linux_family
from .api import register_agent, heartbeat, poll_command, submit_result
from .dispatch import dispatch_action

def load_state():
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {}

def save_state(state):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(state))

def register():
    payload = {
        "mac_address": get_mac_address(),
        "hostname": get_hostname(),
        "os_info": get_linux_family(),
        "bootstrap_secret": BOOTSTRAP_SECRET,
    }

    response = requests.post(
        f"{SERVER_URL.rstrip('/')}/agents/register",
        json=payload,
        timeout=REQUEST_TIMEOUT,
    )

    response.raise_for_status()
    data = response.json()

    auth_data = {
        "agent_id": data["agent_id"],
        "auth_token": data["auth_token"],
        "server_url": SERVER_URL.rstrip("/"),
        "mac_address": get_mac_address(),
    }

    with open("agent_auth.json", "w") as f:
        json.dump(auth_data, f)

    return data

def ensure_registered():
    state = load_state()

    if state.get("agent_id") and state.get("auth_token"):
        return state

    response = register_agent(
        hostname=get_hostname(),
        mac_address=get_mac_address(),
        os_info=get_linux_family(),
        bootstrap_secret=BOOTSTRAP_SECRET,
    )

    state = {
        "agent_id": response["agent_id"],
        "auth_token": response["auth_token"],
    }
    save_state(state)
    return state

def run_loop():
    state = ensure_registered()
    agent_id = state["agent_id"]
    auth_token = state["auth_token"]

    while True:
        try:
            heartbeat(agent_id, auth_token)
            command = poll_command(agent_id, auth_token)

            if command:
                result = dispatch_action(
                    command["action"],
                    command.get("params", {})
                )
                submit_result(
                    command_id=command["id"],
                    auth_token=auth_token,
                    stdout=result.get("stdout", ""),
                    stderr=result.get("stderr", ""),
                    status=result.get("status", "failed"),
                    exit_code=result.get("exit_code", 1),
                )

        except Exception as exc:
            print(f"Agent error: {exc}")

        time.sleep(POLL_INTERVAL)