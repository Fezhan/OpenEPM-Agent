# agent/details.py
import socket
import psutil
from pathlib import Path
import distro


def get_hostname():
    return socket.gethostname()


def get_os_info():
    return distro.id()


def _get_wireless_interface():
    """Try to find a wireless interface via /proc/net/wireless."""
    file = Path("/proc/net/wireless")
    if not file.exists():
        return None
    lines = file.read_text().splitlines()
    for line in lines[2:]:
        line = line.strip()
        if line and ":" in line:
            return line.split(":", 1)[0].strip()
    return None


def _get_any_active_interface():
    """
    Fall back to any active, non-loopback interface that has a MAC address.
    Uses psutil for cross-platform compatibility.
    """
    stats = psutil.net_if_stats()
    addrs = psutil.net_if_addrs()

    for iface, stat in stats.items():
        if iface == "lo" or not stat.isup:
            continue
        for addr in addrs.get(iface, []):
            # AF_LINK (17) on Linux/Mac = MAC address
            if addr.family.name in ("AF_LINK", "AF_PACKET"):
                if addr.address and addr.address != "00:00:00:00:00:00":
                    return iface, addr.address.upper()
    return None, None


def get_mac_address():
    """
    Return the MAC address of the best available network interface.
    Prefers wireless; falls back to any active non-loopback interface.
    """
    # Try wireless first (Linux-specific)
    wireless = _get_wireless_interface()
    if wireless:
        address_file = Path(f"/sys/class/net/{wireless}/address")
        if address_file.exists():
            return address_file.read_text().strip().upper()

    # Fall back to psutil (cross-platform)
    iface, mac = _get_any_active_interface()
    if mac:
        return mac

    raise RuntimeError("No suitable network interface found for MAC address detection")


def get_linux_family():
    distro_id   = distro.id().lower()
    distro_like = distro.like().lower()

    if (distro_id in {"debian", "ubuntu", "linuxmint"}
            or "debian" in distro_like
            or "ubuntu" in distro_like):
        return "debian"

    if (distro_id in {"arch", "manjaro", "endeavouros"}
            or "arch" in distro_like):
        return "arch"

    return "linux"