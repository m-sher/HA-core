"""Constants for the Aruba integration."""

import re
from typing import Final

DOMAIN: Final = "aruba"

DEVICES_REGEX: Final[re.Pattern[str]] = re.compile(
    r"(?P<name>([^\s]+)?)\s+"
    r"(?P<ip>([0-9]{1,3}[\.]){3}[0-9]{1,3})\s+"
    r"(?P<mac>([0-9a-f]{2}[:-]){5}([0-9a-f]{2}))\s+"
)
