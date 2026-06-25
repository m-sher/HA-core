"""The SNMP integration.

Config entries added by this migration are device_tracker-only. The existing
YAML sensor and switch platforms continue to work independently via platform
setup and do not use config entries.
"""

from pysnmp.error import PySnmpError

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .coordinator import SnmpConfigEntry, SnmpDataUpdateCoordinator
from .util import async_get_snmp_engine

__all__ = ["async_get_snmp_engine"]

PLATFORMS = [Platform.DEVICE_TRACKER]


async def async_setup_entry(hass: HomeAssistant, entry: SnmpConfigEntry) -> bool:
    """Set up SNMP device tracker from a config entry."""
    coordinator = SnmpDataUpdateCoordinator(hass, entry)
    try:
        await coordinator.async_setup()
    except (PySnmpError, OSError, TimeoutError, ValueError) as err:
        raise ConfigEntryNotReady(f"Failed to set up SNMP: {err}") from err
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: SnmpConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
