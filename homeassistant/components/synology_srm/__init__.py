"""The Synology SRM integration."""

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .coordinator import SynologySrmConfigEntry, SynologySrmDataUpdateCoordinator

PLATFORMS = [Platform.DEVICE_TRACKER]


async def async_setup_entry(hass: HomeAssistant, entry: SynologySrmConfigEntry) -> bool:
    """Set up Synology SRM from a config entry."""
    coordinator = SynologySrmDataUpdateCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: SynologySrmConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
