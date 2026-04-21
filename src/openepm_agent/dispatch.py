#!/usr/bin/env python
import subprocess
import shlex
import os
from .systemfunctions import run_command
from .details import get_linux_family

# ── Desktop notification helper ───────────────────────────────────────────────

def _notify(title: str, message: str, urgency: str = "normal", icon: str = "dialog-information"):
    """
    Send a libnotify desktop notification.
    urgency: low | normal | critical
    Runs as the logged-in user via DBUS_SESSION_BUS_ADDRESS.
    Silently fails if notify-send is not available.
    """
    try:
        # Find the display session env for the logged-in user
        env = os.environ.copy()

        # Ensure DBUS session is available (needed when agent runs as root/service)
        if "DBUS_SESSION_BUS_ADDRESS" not in env:
            # Try to find it from a running user session
            result = subprocess.run(
                ["pgrep", "-u", env.get("USER", "handesh"), "-x", "Hyprland"],
                capture_output=True, text=True
            )
            pid = result.stdout.strip()
            if pid:
                env_file = f"/proc/{pid}/environ"
                try:
                    with open(env_file, "r") as f:
                        for entry in f.read().split("\0"):
                            if "=" in entry:
                                k, v = entry.split("=", 1)
                                if k in ("DBUS_SESSION_BUS_ADDRESS", "DISPLAY", "WAYLAND_DISPLAY", "XDG_RUNTIME_DIR"):
                                    env[k] = v
                except Exception:
                    pass

        subprocess.Popen(
            ["notify-send", "--urgency", urgency, "--icon", icon, "--app-name", "OpenEPM Agent", title, message],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        pass  # notify-send not installed — silently skip
    except Exception:
        pass


# ── OS-aware command map ──────────────────────────────────────────────────────

SYSTEM_UPDATE_COMMANDS = {
    "arch":   ["sudo", "pacman", "-Syu", "--noconfirm"],
    "debian": ["sudo", "apt-get", "update", "&&", "sudo", "apt-get", "upgrade", "-y"],
    "ubuntu": ["sudo", "apt-get", "update", "&&", "sudo", "apt-get", "upgrade", "-y"],
    "fedora": ["sudo", "dnf", "upgrade", "-y"],
    "rhel":   ["sudo", "dnf", "upgrade", "-y"],
    "centos": ["sudo", "yum", "update", "-y"],
}


# ── Internal command handlers ─────────────────────────────────────────────────

def handle_ping(params, os_family=None):
    _notify("Agent Ping", "Ping received — sending pong.", urgency="low")
    return {
        "status":    "completed",
        "stdout":    "pong",
        "stderr":    "",
        "exit_code": 0,
    }


def handle_get_system_info(params, os_family=None):
    _notify("System Info", "Collecting system information...", urgency="low")
    import platform, socket, json
    import psutil

    info = {
        "hostname":      socket.gethostname(),
        "os":            platform.system(),
        "os_version":    platform.version(),
        "cpu_count":     psutil.cpu_count(logical=True),
        "ram_total_gb":  round(psutil.virtual_memory().total / 1e9, 2),
        "ram_used_pct":  psutil.virtual_memory().percent,
        "disk_total_gb": round(psutil.disk_usage("/").total / 1e9, 2),
        "disk_used_pct": psutil.disk_usage("/").percent,
    }
    _notify("System Info", "System information collected successfully.", urgency="low", icon="dialog-information")
    return {
        "status":    "completed",
        "stdout":    json.dumps(info, indent=2),
        "stderr":    "",
        "exit_code": 0,
    }


def handle_get_process_list(params, os_family=None):
    _notify("Process List", "Collecting running processes...", urgency="low")
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

    _notify("Process List", f"Collected {len(procs)} running processes.", urgency="low")
    return {
        "status":    "completed",
        "stdout":    json.dumps(procs, indent=2),
        "stderr":    "",
        "exit_code": 0,
    }


def handle_restart_agent(params, os_family=None):
    _notify("Agent Restart", "Agent restart has been approved and is now restarting.", urgency="critical", icon="dialog-warning")
    return {
        "status":       "completed",
        "stdout":       "Agent restart initiated.",
        "stderr":       "",
        "exit_code":    0,
        "_post_action": "restart",
    }


def handle_system_update(params, os_family=None):
    family = (os_family or get_linux_family()).lower()
    cmd    = SYSTEM_UPDATE_COMMANDS.get(family)

    if not cmd:
        _notify("System Update Failed", f"No update command defined for OS: '{family}'", urgency="critical", icon="dialog-error")
        return {
            "status":    "failed",
            "stdout":    "",
            "stderr":    f"No system update command defined for OS family: '{family}'",
            "exit_code": 1,
        }

    _notify("System Update", "System update started — this may take a few minutes.", urgency="normal", icon="software-update-available")

    if family in ("debian", "ubuntu"):
        result = run_command("sudo apt-get update && sudo apt-get upgrade -y", shell=True, timeout=300)
    else:
        result = run_command(cmd, shell=False, timeout=300)

    if result.get("status") == "completed":
        _notify("System Update", "System update completed successfully.", urgency="normal", icon="dialog-information")
    else:
        _notify("System Update Failed", result.get("stderr", "Unknown error"), urgency="critical", icon="dialog-error")

    return {
        "status":    result.get("status",    "failed"),
        "stdout":    result.get("stdout",    ""),
        "stderr":    result.get("stderr",    ""),
        "exit_code": result.get("exit_code", 1),
    }


def handle_disk_usage(params, os_family=None):
    path = params.get("path", "/")
    _notify("Disk Usage", f"Checking disk usage for: {path}", urgency="low")
    result = run_command(["df", "-h", path], shell=False, timeout=10)
    return {
        "status":    result.get("status",    "failed"),
        "stdout":    result.get("stdout",    ""),
        "stderr":    result.get("stderr",    ""),
        "exit_code": result.get("exit_code", 1),
    }


def handle_collect_logs(params, os_family=None):
    log_path = params.get("log_path", "/var/log/syslog")
    lines    = str(params.get("lines", 50))
    _notify("Log Collection", f"Collecting last {lines} lines from {log_path}", urgency="low")
    result = run_command(["tail", "-n", lines, log_path], shell=False, timeout=15)
    return {
        "status":    result.get("status",    "failed"),
        "stdout":    result.get("stdout",    ""),
        "stderr":    result.get("stderr",    ""),
        "exit_code": result.get("exit_code", 1),
    }


def handle_check_open_ports(params, os_family=None):
    _notify("Port Scan", "Checking open ports...", urgency="low")
    result = run_command(["ss", "-tuln"], shell=False, timeout=10)
    return {
        "status":    result.get("status",    "failed"),
        "stdout":    result.get("stdout",    ""),
        "stderr":    result.get("stderr",    ""),
        "exit_code": result.get("exit_code", 1),
    }


def handle_get_service_status(params, os_family=None):
    service = params.get("service_name")
    if not service:
        _notify("Service Status Failed", "No service name provided.", urgency="critical", icon="dialog-error")
        return {"status": "failed", "stdout": "", "stderr": "Missing service_name parameter", "exit_code": 1}
    _notify("Service Status", f"Checking status of service: {service}", urgency="low")
    result = run_command(["systemctl", "status", service], shell=False, timeout=10)
    status_text = "running" if result.get("exit_code") == 0 else "not running or failed"
    _notify("Service Status", f"{service} is {status_text}.", urgency="low")
    return {
        "status":    result.get("status",    "failed"),
        "stdout":    result.get("stdout",    ""),
        "stderr":    result.get("stderr",    ""),
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
    for key, value in parameters.items():
        template = template.replace(f"{{{{{key}}}}}", str(value))
    return template


def _run_shell(template: str, parameters: dict, timeout: int = 30) -> dict:
    cmd_str = _render_template(template, parameters)
    try:
        args   = shlex.split(cmd_str)
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
        return {"status": "timeout", "stdout": "", "stderr": "Command timed out", "exit_code": -1}
    except Exception as e:
        return {"status": "failed",  "stdout": "", "stderr": str(e),              "exit_code": 1}


# ── Main dispatcher ───────────────────────────────────────────────────────────

def dispatch_command(execution: dict, os_family: str = None) -> dict:
    """
    Entry point called by runner.py.
    os_family is passed in from enrollment so handlers can make OS-aware decisions.
    """
    definition   = execution.get("definition", {})
    command_type = definition.get("command_type", "")
    name         = definition.get("name", "")
    template     = definition.get("command_template", "")
    parameters   = execution.get("parameters", {})
    timeout      = definition.get("timeout_seconds", 30)

    if command_type == "internal":
        handler = INTERNAL_HANDLERS.get(name)
        if not handler:
            return {
                "status":    "failed",
                "stdout":    "",
                "stderr":    f"Unknown internal command: {name}",
                "exit_code": 1,
            }
        return handler(parameters, os_family=os_family)

    elif command_type == "shell":
        return _run_shell(template, parameters, timeout=timeout)

    else:
        return {
            "status":    "failed",
            "stdout":    "",
            "stderr":    f"Unsupported command type: {command_type}",
            "exit_code": 1,
        }