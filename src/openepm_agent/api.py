import requests
from .config import SERVER_URL


def register_agent(hostname, bootstrap_secret, os_info, mac_address):
    response = requests.post(
        f"{SERVER_URL}/agents/register",
        json={
            "hostname": hostname,
            "bootstrap_secret": bootstrap_secret,
            "os_info": os_info,
            "mac_address": mac_address
        },
        timeout=10,
    )
    response.raise_for_status()
    return response.json()["agent"]


def heartbeat(agent_id, auth_token):
    response = requests.post(
        f"{SERVER_URL}/agents/{agent_id}/heartbeat",
        headers=auth_headers(auth_token),
        timeout=10)
    response.raise_for_status()
    return response.json()


def poll_command(agent_id, auth_token):
    response = requests.get(
        f"{SERVER_URL}/agents/{agent_id}/commands",
        headers=auth_headers(auth_token),
        timeout=30)
    response.raise_for_status()
    return response.json().get("command")


def submit_result(command_id, auth_token, stdout, stderr, status, exit_code):
    response = requests.post(
        f"{SERVER_URL}/commands/{command_id}/result",
        headers=auth_headers(auth_token),
        json={
            "stdout": stdout,
            "stderr": stderr,
            "status": status,
            "exit_code": exit_code,
        },
        timeout=10,
    )
    response.raise_for_status()
    return response.json()

def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}