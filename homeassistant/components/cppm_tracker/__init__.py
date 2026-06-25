"""The Aruba ClearPass integration."""

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .coordinator import CPPMConfigEntry, CPPMDataUpdateCoordinator

PLATFORMS = [Platform.DEVICE_TRACKER]


async def async_setup_entry(hass: HomeAssistant, entry: CPPMConfigEntry) -> bool:
    """Set up Aruba ClearPass from a config entry."""
    coordinator = CPPMDataUpdateCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: CPPMConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
