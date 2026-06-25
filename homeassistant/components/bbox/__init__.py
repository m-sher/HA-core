"""The Bbox integration."""

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .coordinator import BboxConfigEntry, BboxDataUpdateCoordinator

PLATFORMS = [Platform.DEVICE_TRACKER]


async def async_setup_entry(hass: HomeAssistant, entry: BboxConfigEntry) -> bool:
    """Set up Bbox from a config entry."""
    coordinator = BboxDataUpdateCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: BboxConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
