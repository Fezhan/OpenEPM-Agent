import socket
import uuid
import distro

def get_hostname():
    return socket.gethostname()

def get_os_info():
    return distro.id()

def get_mac_address():
    mac_num = uuid.getnode()
    return ":".join(f"{(mac_num >> shift) & 0xff:02X}" for shift in range(40, -1, -8))

def get_linux_family():
    distro_id = distro.id().lower()
    distro_like = distro.like().lower()

    if distro_id in {"debian", "ubuntu", "linuxmint"} or "debian" in distro_like or "ubuntu" in distro_like:
        return "debian"

    if distro_id in {"arch", "manjaro", "endeavouros"} or "arch" in distro_like:
        return "arch"

    return "linux"