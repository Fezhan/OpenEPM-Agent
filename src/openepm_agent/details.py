import socket
import platform
import uuid

def get_hostname():
    return socket.gethostname()

def get_os_info():
    return platform.platform()

def get_mac_address():
    mac_num = uuid.getnode()
    mac = ":".join(f"{(mac_num >> ele) & 0xff:02X}" for ele in range(40, -1, -8))
    return mac

