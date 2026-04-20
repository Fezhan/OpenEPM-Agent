import json
import time
import requests

from .config import CONFIG_DIR, CONFIG_FILE, POLL_INTERVAL, BOOTSTRAP_SECRET
from .details import get_hostname, get_mac_address, get_linux_family
from .api import register_agent, heartbeat, poll_command, submit_result
from .dispatch import dispatch_action

ENROLL_RETRY_INTERVAL = 60


def load_state():
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {}


def save_state(state):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(state))


def ensure_registered():
    """
    Returns state dict with agent_id/auth_token or None if enrollment failed.
    Never retries here; run_loop decides what to do.
    """
    state = load_state()

    if state.get("agent_id") and state.get("auth_token"):
        return state

    try:
        response = register_agent(
            hostname=get_hostname(),
            mac_address=get_mac_address(),
            os_info=get_linux_family(),
            bootstrap_secret=BOOTSTRAP_SECRET,
        )
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response else None
        body = exc.response.text if exc.response else ""
        print(f"Enrollment HTTP error: {status} {body}")

        # 409 means the server thinks this device is already enrolled.
        # In that case, do NOT keep hammering /agents/register.
        if status == 409:
            print("Device already enrolled according to server; "
                  "will not retry enrollment in this process.")
            return None

        # For other errors (403, 500, etc.), caller decides whether to retry.
        return None

    state = {
        "agent_id": response["agent_id"],
        "auth_token": response["auth_token"],
    }
    save_state(state)
    return state


def run_loop():
    state = None

    while True:
        try:
            if not state:
                state = ensure_registered()
                if state:
                    print(f"Enrollment successful: agent_id={state['agent_id']}")
                else:
                    # No state yet; either not approved, secret wrong, or 409 path.
                    print("Enrollment failed or already enrolled; "
                          "retrying enrollment in 60 seconds...")
                    time.sleep(ENROLL_RETRY_INTERVAL)
                    continue

            agent_id = state["agent_id"]
            auth_token = state["auth_token"]

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

            time.sleep(POLL_INTERVAL)

        except Exception as exc:
            print(f"Agent error: {exc}")

            if not state:
                print("Enrollment failed, retrying in 60 seconds...")
                time.sleep(ENROLL_RETRY_INTERVAL)
            else:
                time.sleep(POLL_INTERVAL)