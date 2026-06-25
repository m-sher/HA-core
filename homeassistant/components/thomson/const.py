"""Constants for the Thomson integration."""

import re

DOMAIN = "thomson"

DEVICES_REGEX = re.compile(
    r"(?P<mac>(([0-9a-f]{2}[:-]){5}([0-9a-f]{2})))\s"
    r"(?P<ip>([0-9]{1,3}[\.]){3}[0-9]{1,3})\s+"
    r"(?P<status>([^\s]+))\s+"
    r"(?P<type>([^\s]+))\s+"
    r"(?P<intf>([^\s]+))\s+"
    r"(?P<hwintf>([^\s]+))\s+"
    r"(?P<host>([^\s]+))"
)
