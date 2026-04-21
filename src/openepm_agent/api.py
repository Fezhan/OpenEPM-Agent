#!/usr/bin/env python
import requests
from .config import SERVER_URL


def register_agent(hostname, mac_address, os_info, bootstrap_secret):
    response = requests.post(
        f"{SERVER_URL}/agents/register",
        json={
            "hostname": hostname,
            "mac_address": mac_address,
            "os_info": os_info,
            "bootstrap_secret": bootstrap_secret,
        },
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def heartbeat(agent_id, auth_token):
    response = requests.post(
        f"{SERVER_URL}/agents/{agent_id}/heartbeat",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def poll_command(agent_id, auth_token):
    response = requests.get(
        f"{SERVER_URL}/agents/{agent_id}/commands",
        headers={"Authorization": f"Bearer {auth_token}"},
        timeout=30,
    )
    response.raise_for_status()
    return response.json().get("command")


def submit_result(execution_id, auth_token, output, error, status, exit_code):
    """
    Post command result back to the server.
    Field names match the server's submit_result route:
      output -> stored in Command/CommandExecution.output
      error  -> stored in Command/CommandExecution.error
    """
    response = requests.post(
        f"{SERVER_URL}/commands/{execution_id}/result",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "output":    output,
            "error":     error,
            "status":    status,
            "exit_code": exit_code,
        },
        timeout=10,
    )
    response.raise_for_status()
    return response.json()