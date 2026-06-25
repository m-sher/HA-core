"""The BT Home Hub 5 integration."""

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .coordinator import BtHomeHub5ConfigEntry, BtHomeHub5DataUpdateCoordinator

PLATFORMS = [Platform.DEVICE_TRACKER]


async def async_setup_entry(hass: HomeAssistant, entry: BtHomeHub5ConfigEntry) -> bool:
    """Set up BT Home Hub 5 from a config entry."""
    coordinator = BtHomeHub5DataUpdateCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: BtHomeHub5ConfigEntry
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
