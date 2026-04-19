import socket
from pathlib import Path
import distro

def get_hostname():
    return socket.gethostname()

def get_os_info():
    return distro.id()

def get_wireless_interface():
    file = Path("/proc/net/wireless")

    if not file.exists():
        raise RuntimeError("/proc/net/wireless not found")

    lines = file.read_text().splitlines()

    for line in lines[2:]:
        line = line.strip()
        if not line:
            continue
        if ":" in line:
            return line.split(":", 1)[0].strip()

    raise RuntimeError("No wireless interface found in /proc/net/wireless")

def get_mac_address():


def get_linux_family():
    distro_id = distro.id().lower()
    distro_like = distro.like().lower()

    if distro_id in {"debian", "ubuntu", "linuxmint"} or "debian" in distro_like or "ubuntu" in distro_like:
        return "debian"

    if distro_id in {"arch", "manjaro", "endeavouros"} or "arch" in distro_like:
        return "arch"

    return "linux"