"""The OpenWrt (luci) integration."""

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .coordinator import LuciConfigEntry, LuciDataUpdateCoordinator

PLATFORMS = [Platform.DEVICE_TRACKER]


async def async_setup_entry(hass: HomeAssistant, entry: LuciConfigEntry) -> bool:
    """Set up OpenWrt (luci) from a config entry."""
    coordinator = LuciDataUpdateCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: LuciConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
