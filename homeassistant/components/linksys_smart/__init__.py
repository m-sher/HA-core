"""The Linksys Smart Wi-Fi integration."""

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .coordinator import LinksysSmartConfigEntry, LinksysSmartDataUpdateCoordinator

PLATFORMS = [Platform.DEVICE_TRACKER]


async def async_setup_entry(
    hass: HomeAssistant, entry: LinksysSmartConfigEntry
) -> bool:
    """Set up Linksys Smart Wi-Fi from a config entry."""
    coordinator = LinksysSmartDataUpdateCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: LinksysSmartConfigEntry
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
