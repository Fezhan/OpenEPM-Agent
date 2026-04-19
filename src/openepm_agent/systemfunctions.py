import subprocess

from .details import get_linux_family

def run_command(cmd, shell=False, timeout=3600):
    """
    Run a system command and return a structured result.
    """
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

def system_update(params=None):
    """
    Perform a full system update on Linux.
    For now supports Debian-based and Arch-based systems.
    """
    params = params or {}
    family = get_linux_family()

    if family == "arch":
        # Arch: full system upgrade, partial upgrades are discouraged [web:676][web:810].
        cmd = "sudo pacman -Syu --noconfirm"
        return run_command(cmd, shell=True, timeout=7200)

    if family == "debian":
        # Debian/Ubuntu: update, upgrade, full-upgrade, autoremove [web:812][web:813].
        cmd = (
            "sudo apt update && "
            "sudo apt upgrade -y && "
            "sudo apt full-upgrade -y && "
            "sudo apt autoremove -y"
        )
        return run_command(cmd, shell=True, timeout=7200)

    return {
        "status": "failed",
        "stdout": "",
        "stderr": f"Unsupported Linux family for system_update: {family}",
        "exit_code": 1,
    }