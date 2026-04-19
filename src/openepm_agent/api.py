import requests
from .config import SERVER_URL


def register_agent(hostname, bootstrap_secret, os_type, mac_address):
    response = requests.post(
        f"{SERVER_URL}/agents/register",
        json={
            "hostname": hostname,
            "bootstrap_secret": bootstrap_secret,
            "os_type": os_type,
            "mac_address": mac_address
        },
        timeout=10,
    )
    response.raise_for_status()
    return response.json()["agent"]


def heartbeat(agent_id):
    response = requests.post(f"{SERVER_URL}/agents/{agent_id}/heartbeat", timeout=10)
    response.raise_for_status()
    return response.json()


def poll_command(agent_id):
    response = requests.get(f"{SERVER_URL}/agents/{agent_id}/commands", timeout=30)
    response.raise_for_status()
    return response.json().get("command")


def submit_result(command_id, output, status):
    response = requests.post(
        f"{SERVER_URL}/commands/{command_id}/result",
        json={"output": output, "status": status},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()

def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}