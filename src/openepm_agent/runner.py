#!/usr/bin/env python
import json
import os
import sys
import time
import requests

from .config import CONFIG_DIR, CONFIG_FILE, POLL_INTERVAL, BOOTSTRAP_SECRET, ENROLL_RETRY_INTERVAL
from .details import get_hostname, get_mac_address, get_linux_family
from .api import register_agent, heartbeat, poll_command, submit_result
from .dispatch import dispatch_command


def load_state():
    try:
        if CONFIG_FILE.exists():
            text = CONFIG_FILE.read_text()
            if not text.strip():
                return {}
            return json.loads(text)
    except json.JSONDecodeError as exc:
        print(f"[agent] load_state failed: {exc}; ignoring corrupt state file")
    except Exception as exc:
        print(f"[agent] load_state unexpected error: {exc}")
    return {}


def save_state(state):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(state))


def ensure_registered():
    state = load_state()

    if state.get("agent_id") and state.get("auth_token"):
        return state

    os_family = get_linux_family()

    try:
        response = register_agent(
            hostname=get_hostname(),
            mac_address=get_mac_address(),
            os_info=os_family,
            bootstrap_secret=BOOTSTRAP_SECRET,
        )
        state = {
            "agent_id":   response["agent_id"],
            "auth_token": response["auth_token"],
            "os_family":  os_family,
        }
        save_state(state)
        return state

    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else None
        body   = exc.response.text        if exc.response is not None else ""
        print(f"[agent] Enrollment HTTP error: {status} {body}")
        if status == 409:
            print("[agent] Server says this device is already enrolled but no local state exists.")
            print("[agent] Remove the device on the server or restore agent.conf manually.")
        return None

    except KeyError as exc:
        print(f"[agent] Enrollment response missing field: {exc}")
        return None

    except Exception as exc:
        print(f"[agent] Enrollment error: {exc}")
        return None


def run_loop():
    state = None

    while True:
        try:
            # ── Enrollment ────────────────────────────────────────────────────
            if not state:
                state = ensure_registered()
                if state:
                    print(f"[agent] Enrolled: agent_id={state['agent_id']}, os_family={state.get('os_family', 'unknown')}")
                else:
                    print(f"[agent] Enrollment failed. Retrying in {ENROLL_RETRY_INTERVAL}s...")
                    time.sleep(ENROLL_RETRY_INTERVAL)
                    continue

            agent_id   = state["agent_id"]
            auth_token = state["auth_token"]
            os_family  = state.get("os_family") or get_linux_family()

            # ── Heartbeat ─────────────────────────────────────────────────────
            heartbeat(agent_id, auth_token)

            # ── Poll for command ──────────────────────────────────────────────
            command = poll_command(agent_id, auth_token)

            if command:
                execution_id = command["execution_id"]
                name         = command.get("definition", {}).get("name", "unknown")
                print(f"[agent] Executing: {name} (execution_id={execution_id})")

                result = dispatch_command(command, os_family=os_family)

                submit_result(
                    execution_id=execution_id,
                    auth_token=auth_token,
                    output=result.get("stdout", ""),
                    error=result.get("stderr",  ""),
                    status=result.get("status",  "failed"),
                    exit_code=result.get("exit_code", 1),
                )
                print(f"[agent] Result submitted: {result['status']}")

                post_action = result.get("_post_action")
                if post_action == "restart":
                    print("[agent] Restarting agent process...")
                    os.execv(sys.executable, [sys.executable] + sys.argv)

            time.sleep(POLL_INTERVAL)

        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else None
            print(f"[agent] HTTP error: {status}")
            if status == 401:
                print("[agent] Auth token rejected. Clearing state and re-enrolling...")
                state = None
                if CONFIG_FILE.exists():
                    CONFIG_FILE.unlink()
            time.sleep(POLL_INTERVAL)

        except Exception as exc:
            print(f"[agent] Error: {exc}")
            time.sleep(POLL_INTERVAL)