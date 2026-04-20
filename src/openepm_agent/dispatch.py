# agent/dispatch.py
import subprocess
import shlex
from .systemfunctions import system_update, run_command
from .details import get_linux_family


# ── Internal command handlers ─────────────────────────────────────────────────

def handle_ping(params):
    return {
        "status":    "completed",
        "stdout":    "pong",
        "stderr":    "",
        "exit_code": 0,
    }


def handle_get_system_info(params):
    import platform, socket, json
    import psutil

    info = {
        "hostname":    socket.gethostname(),
        "os":          platform.system(),
        "os_version":  platform.version(),
        "cpu_count":   psutil.cpu_count(logical=True),
        "ram_total_gb": round(psutil.virtual_memory().total / 1e9, 2),
        "ram_used_pct": psutil.virtual_memory().percent,
        "disk_total_gb": round(psutil.disk_usage("/").total / 1e9, 2),
        "disk_used_pct": psutil.disk_usage("/").percent,
    }
    return {
        "status":    "completed",
        "stdout":    json.dumps(info, indent=2),
        "stderr":    "",
        "exit_code": 0,
    }


def handle_get_process_list(params):
    import json, psutil

    procs = []
    for p in psutil.process_iter(["pid", "name", "status", "username"]):
        try:
            procs.append({
                "pid":      p.info["pid"],
                "name":     p.info["name"],
                "status":   p.info["status"],
                "username": p.info["username"],
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    return {
        "status":    "completed",
        "stdout":    json.dumps(procs, indent=2),
        "stderr":    "",
        "exit_code": 0,
    }


def handle_restart_agent(params):
    """
    Returns success to the server first; actual restart happens in runner.py
    after the result has been submitted.
    """
    return {
        "status":    "completed",
        "stdout":    "Agent restart initiated.",
        "stderr":    "",
        "exit_code": 0,
        "_post_action": "restart",  # runner.py will check for this
    }


def handle_system_update(params):
    result = system_update(params)
    return {
        "status":    result.get("status", "failed"),
        "stdout":    result.get("stdout", ""),
        "stderr":    result.get("stderr", ""),
        "exit_code": result.get("exit_code", 1),
    }


def handle_disk_usage(params):
    path = params.get("path", "/")
    result = run_command(["df", "-h", path], shell=False, timeout=10)
    return {
        "status":    result.get("status", "failed"),
        "stdout":    result.get("stdout", ""),
        "stderr":    result.get("stderr", ""),
        "exit_code": result.get("exit_code", 1),
    }


def handle_collect_logs(params):
    log_path = params.get("log_path", "/var/log/syslog")
    lines    = str(params.get("lines", 50))
    result   = run_command(["tail", "-n", lines, log_path], shell=False, timeout=15)
    return {
        "status":    result.get("status", "failed"),
        "stdout":    result.get("stdout", ""),
        "stderr":    result.get("stderr", ""),
        "exit_code": result.get("exit_code", 1),
    }


def handle_check_open_ports(params):
    result = run_command(["ss", "-tuln"], shell=False, timeout=10)
    return {
        "status":    result.get("status", "failed"),
        "stdout":    result.get("stdout", ""),
        "stderr":    result.get("stderr", ""),
        "exit_code": result.get("exit_code", 1),
    }


def handle_get_service_status(params):
    service = params.get("service_name")
    if not service:
        return {"status": "failed", "stdout": "", "stderr": "Missing service_name parameter", "exit_code": 1}
    result = run_command(["systemctl", "status", service], shell=False, timeout=10)
    return {
        "status":    result.get("status", "failed"),
        "stdout":    result.get("stdout", ""),
        "stderr":    result.get("stderr", ""),
        "exit_code": result.get("exit_code", 1),
    }


# ── Registry ──────────────────────────────────────────────────────────────────

INTERNAL_HANDLERS = {
    "ping":               handle_ping,
    "get_system_info":    handle_get_system_info,
    "get_process_list":   handle_get_process_list,
    "restart_agent":      handle_restart_agent,
    "system_update":      handle_system_update,
    "disk_usage":         handle_disk_usage,
    "collect_logs":       handle_collect_logs,
    "check_open_ports":   handle_check_open_ports,
    "get_service_status": handle_get_service_status,
}


# ── Shell executor ────────────────────────────────────────────────────────────

def _render_template(template: str, parameters: dict) -> str:
    """Substitute {{key}} placeholders with parameter values."""
    for key, value in parameters.items():
        template = template.replace(f"{{{{{key}}}}}", str(value))
    return template


def _run_shell(template: str, parameters: dict, timeout: int = 30) -> dict:
    """
    Render the command template and run it.
    Uses shell=False where possible to reduce injection risk.
    Falls back to shell=True only for complex pipelines.
    """
    cmd_str = _render_template(template, parameters)
    try:
        # Use shlex.split for safe tokenisation when not using shell
        args = shlex.split(cmd_str)
        result = subprocess.run(
            args,
            shell=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return {
            "status":    "completed" if result.returncode == 0 else "failed",
            "stdout":    result.stdout,
            "stderr":    result.stderr,
            "exit_code": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"status": "timeout",  "stdout": "", "stderr": "Command timed out", "exit_code": -1}
    except Exception as e:
        return {"status": "failed",   "stdout": "", "stderr": str(e),              "exit_code": 1}


# ── Main dispatcher ───────────────────────────────────────────────────────────

def dispatch_command(execution: dict) -> dict:
    """
    Entry point called by runner.py.
    Expects the execution dict from the server's poll response:
      {
        "execution_id": int,
        "definition": { "name": str, "command_type": str, "command_template": str, ... },
        "parameters": { ... }
      }
    """
    definition    = execution.get("definition", {})
    command_type  = definition.get("command_type", "")
    name          = definition.get("name", "")
    template      = definition.get("command_template", "")
    parameters    = execution.get("parameters", {})
    timeout       = definition.get("timeout_seconds", 30)

    if command_type == "internal":
        handler = INTERNAL_HANDLERS.get(name)
        if not handler:
            return {
                "status":    "failed",
                "stdout":    "",
                "stderr":    f"Unknown internal command: {name}",
                "exit_code": 1,
            }
        return handler(parameters)

    elif command_type == "shell":
        return _run_shell(template, parameters, timeout=timeout)

    else:
        return {
            "status":    "failed",
            "stdout":    "",
            "stderr":    f"Unsupported command type: {command_type}",
            "exit_code": 1,
        }