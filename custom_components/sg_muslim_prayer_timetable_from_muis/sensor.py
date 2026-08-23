import datetime
import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the SG Muslim Prayer Timetable from MUIS sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    prayers = ["Subuh", "Syuruk", "Zohor", "Asar", "Maghrib", "Isyak"]
    entities = [
        MuslimPrayerSensor(coordinator, prayer)
        for prayer in prayers
    ]
    entities.append(MuslimPrayerStatusSensor(coordinator))
    
    async_add_entities(entities, update_before_add=True)

class MuslimPrayerSensor(SensorEntity):
    """Representation of a Muslim Prayer Time sensor."""

    def __init__(self, coordinator, prayer_name):
        self.coordinator = coordinator
        self.prayer_name = prayer_name
        self._attr_name = f"{prayer_name} Prayer"
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{prayer_name.lower()}_prayer"
        self._attr_device_class = "timestamp"
        self.entity_id = f"sensor.sg_muis_{prayer_name.lower()}_prayer"


    @property
    def native_value(self):
        """Return the next upcoming timestamp for this specific prayer."""
        now = dt_util.now()
        today_str = now.strftime("%Y-%m-%d")
        tomorrow_str = (now + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        
        # 1. Retrieve today's schedule
        today_sched = self.coordinator.get_schedule_for_date(today_str)
        if today_sched:
            time_str = today_sched.get(self.prayer_name)
            if time_str:
                # Parse hour and minute (HH:MM)
                hour, minute = map(int, time_str.split(":"))
                
                # Convert Zohor, Asar, Maghrib, Isyak to 24-hour format if in 12-hour format
                if self.prayer_name in ["Zohor", "Asar", "Maghrib", "Isyak"]:
                    if hour < 12:
                        if self.prayer_name == "Zohor" and hour < 11:
                            hour += 12
                        elif self.prayer_name != "Zohor":
                            hour += 12
                
                # Construct datetime object for today's prayer (SG is UTC+8)
                tz = datetime.timezone(datetime.timedelta(hours=8))
                prayer_time_today = datetime.datetime(
                    now.year, now.month, now.day, hour, minute, 0, tzinfo=tz
                )
                
                # If prayer time has not passed yet, return it
                if now < prayer_time_today:
                    return prayer_time_today

        # 2. If today's prayer has passed (or today's data is missing), roll over to tomorrow
        tomorrow_sched = self.coordinator.get_schedule_for_date(tomorrow_str)
        if tomorrow_sched:
            time_str_tomorrow = tomorrow_sched.get(self.prayer_name)
            if time_str_tomorrow:
                hour_t, minute_t = map(int, time_str_tomorrow.split(":"))
                
                if self.prayer_name in ["Zohor", "Asar", "Maghrib", "Isyak"]:
                    if hour_t < 12:
                        if self.prayer_name == "Zohor" and hour_t < 11:
                            hour_t += 12
                        elif self.prayer_name != "Zohor":
                            hour_t += 12
                
                tomorrow_date = now + datetime.timedelta(days=1)
                tz = datetime.timezone(datetime.timedelta(hours=8))
                prayer_time_tomorrow = datetime.datetime(
                    tomorrow_date.year, tomorrow_date.month, tomorrow_date.day,
                    hour_t, minute_t, 0, tzinfo=tz
                )
                return prayer_time_tomorrow

        # 3. Graceful Failure: If no data is available, return None (reports as 'unavailable' in HA)
        return None

class MuslimPrayerStatusSensor(SensorEntity):
    """Sensor to report the sync and data status of Muslim Prayer Timetables."""

    def __init__(self, coordinator):
        self.coordinator = coordinator
        self._attr_name = "Muslim Prayers Last Sync"
        self._attr_unique_id = f"{coordinator.entry.entry_id}_last_sync"
        self.entity_id = "sensor.sg_muis_last_sync"

    @property
    def native_value(self):
        """Return the sync status."""
        today = datetime.date.today()
        # Verify if current year's data is loaded
        if not self.coordinator.data:
            return "missing_schedule_data"
        
        # If in November/December, verify next year's schedule status
        if today.month in [11, 12]:
            if not self.coordinator.next_year_data:
                return "awaiting_next_year_schedule"
            
        return self.coordinator.sync_status

    @property
    def extra_state_attributes(self):
        """Return diagnostic state attributes."""
        return {
            "last_sync_success": self.coordinator.last_sync_success,
            "collection_id": self.coordinator.collection_id,
            "has_current_year_data": len(self.coordinator.data) > 0,
            "has_next_year_data": len(self.coordinator.next_year_data) > 0,
            "current_year_records_count": len(self.coordinator.data),
            "next_year_records_count": len(self.coordinator.next_year_data),
        }

