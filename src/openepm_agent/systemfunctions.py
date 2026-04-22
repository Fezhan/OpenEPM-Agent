#!/usr/bin/env python
import subprocess

from .details import get_linux_family

def run_command(cmd, shell=False, timeout=3600):
    """
    Run a system command and return a structured result.
    """
    print(f"[agent] run_command: cmd={cmd!r}, shell={shell}, timeout={timeout}")
    try:
        result = subprocess.run(
            cmd,
            shell=shell,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return {
            "status": "success" if result.returncode == 0 else "failed",
            "stdout": result.stdout or "",
            "stderr": result.stderr or "",
            "exit_code": result.returncode,
        }
    except subprocess.TimeoutExpired as e:
        return {
            "status": "failed",
            "stdout": e.stdout or "",
            "stderr": (e.stderr or "") + "\nCommand timed out.",
            "exit_code": -1,
        }
    except Exception as e:
        return {
            "status": "failed",
            "stdout": "",
            "stderr": str(e),
            "exit_code": 1,
        }