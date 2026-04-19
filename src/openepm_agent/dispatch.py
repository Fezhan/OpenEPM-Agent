import platform
import subprocess
from .systemfunctions import system_update

def dispatch_action(action, params=None):
    params = params or {}
    handlers = {
        "system_update": system_update, # To-implement
    }

    handler = handlers.get(action)
    if not handler:
        return {
            "status": "failed",
            "stdout": "",
            "stderr": f"Unsupported action: {action}",
            "exit_code": 1,
        }

    return handler(params)