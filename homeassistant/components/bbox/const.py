"""Constants for the Bbox integration."""

from typing import NamedTuple

DOMAIN = "bbox"

DEFAULT_HOST = "192.168.1.254"


class Device(NamedTuple):
    """Representation of a connected Bbox device."""

    mac: str
    name: str
    ip: str
