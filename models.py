from dataclasses import dataclass


@dataclass
class Host:
    ip_address: str
    mac_address: str
    vendor: str
    last_seen: str
