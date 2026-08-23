import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import MuslimPrayerCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up SG Muslim Prayer Timetable from MUIS from a config entry."""
    coordinator = MuslimPrayerCoordinator(hass, entry)
    
    # Initialize coordinator (loads cache or fetches from API)
    await coordinator.async_setup()
    
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # Forward the setup to sensors
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_forward_entry_unload(entry, "sensor")
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
