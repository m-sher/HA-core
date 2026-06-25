"""The Arris TG2492LG integration."""

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .coordinator import ArrisTg2492lgConfigEntry, ArrisTg2492lgDataUpdateCoordinator

PLATFORMS = [Platform.DEVICE_TRACKER]


async def async_setup_entry(
    hass: HomeAssistant, entry: ArrisTg2492lgConfigEntry
) -> bool:
    """Set up Arris TG2492LG from a config entry."""
    coordinator = ArrisTg2492lgDataUpdateCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: ArrisTg2492lgConfigEntry
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
