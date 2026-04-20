import json
import time
import requests

from .config import CONFIG_DIR, CONFIG_FILE, POLL_INTERVAL, BOOTSTRAP_SECRET
from .details import get_hostname, get_mac_address, get_linux_family
from .api import register_agent, heartbeat, poll_command, submit_result
from .dispatch import dispatch_action

ENROLL_RETRY_INTERVAL = 60


def load_state():
    try:
        if CONFIG_FILE.exists():
            text = CONFIG_FILE.read_text()
            if not text.strip():
                # Empty file; treat as no state
                return {}
            return json.loads(text)
    except json.JSONDecodeError as exc:
        print(f"load_state failed: {exc}; ignoring corrupt state file")
        return {}
    except Exception as exc:
        print(f"load_state unexpected error: {exc}")
        return {}
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

        state = {
            "agent_id": response["agent_id"],
            "auth_token": response["auth_token"],
        }
        save_state(state)
        return state

    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else None
        body = exc.response.text if exc.response is not None else ""
        print(f"Enrollment HTTP error: {status} {body}")

        if status == 409:
            print("Server says this device is already enrolled, but no local state exists.")
            print("Delete the existing device on the server or implement credential recovery.")
        return None

    except KeyError as exc:
        print(f"Enrollment response missing field: {exc}")
        return None

    except Exception as exc:
        print(f"Enrollment error: {exc}")
        return None

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