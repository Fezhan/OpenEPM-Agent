import json
import subprocess
import time
from pathlib import Path
from .config import (
    CONFIG_DIR,
    CONFIG_FILE,
    POLL_INTERVAL,
    get_hostname,
    get_ip_address,
    get_os_type,
)
from .api import register_agent, heartbeat, poll_command, submit_result


def load_agent_id():
    if CONFIG_FILE.exists():
        data = json.loads(CONFIG_FILE.read_text())
        return data.get("agent_id")
    return None


def save_agent_id(agent_id):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps({"agent_id": agent_id}))


def ensure_registered():
    agent_id = load_agent_id()
    if agent_id:
        return agent_id

    agent = register_agent(
        hostname=get_hostname(),
        ip_address=get_ip_address(),
        os_type=get_os_type(),
    )
    save_agent_id(agent["id"])
    return agent["id"]


def execute_command(command_text):
    try:
        result = subprocess.run(
            command_text,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60,
        )
        output = (result.stdout or "") + (result.stderr or "")
        status = "completed" if result.returncode == 0 else "failed"
        return output.strip(), status
    except Exception as exc:
        return str(exc), "failed"


def run_loop():
    agent_id = ensure_registered()
    while True:
        try:
            heartbeat(agent_id)
            command = poll_command(agent_id)
            if command:
                output, status = execute_command(command["command_text"])
                submit_result(command["id"], output, status)
        except Exception as exc:
            print(f"Agent error: {exc}")
        time.sleep(POLL_INTERVAL)
