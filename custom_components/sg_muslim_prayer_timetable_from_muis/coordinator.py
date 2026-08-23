import os
import logging
import datetime
from datetime import timedelta
import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.storage import Store
from homeassistant.helpers.event import async_track_time_interval

from .const import DOMAIN, CONF_COLLECTION_ID

_LOGGER = logging.getLogger(__name__)

class MuslimPrayerCoordinator:
    """Class to manage fetching and caching SG Muslim Prayer Timetable from MUIS."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        self.hass = hass
        self.entry = entry
        self.collection_id = entry.data.get(CONF_COLLECTION_ID)
        
        self.data = []  # Current year's data records
        self.next_year_data = []  # Preloaded next year's data (used in Dec)
        self.last_sync_success = None
        self.sync_status = "initial"
        self._periodic_listener = None
        self._last_next_year_check = None

    async def async_setup(self):
        """Set up the coordinator."""
        # 1. Load current year's cached data or fetch if missing
        await self.async_load_current_year_data()

        # 2. Register periodic listener to check/retry fetching data (every 2 hours)
        self._periodic_listener = async_track_time_interval(
            self.hass, self.async_periodic_check, timedelta(hours=2)
        )
        
        # Trigger an immediate check at startup
        await self.async_periodic_check(datetime.datetime.now())

    def _get_store(self, year: int) -> Store:
        """Get the storage helper for a specific year."""
        return Store(self.hass, 1, f"muslim_prayers_{year}")

    async def async_load_current_year_data(self):
        """Load current year's data from cache, or fetch it if missing."""
        today = datetime.date.today()
        current_year = today.year
        
        # Load current year cache
        store = self._get_store(current_year)
        cached_data = await store.async_load()
        if cached_data:
            _LOGGER.info("Loaded cached Muslim Prayer times for %s", current_year)
            self.data = cached_data.get("records", [])
            self.last_sync_success = cached_data.get("last_sync")
            self.sync_status = "success"
        else:
            _LOGGER.warning("No cache found for %s. Fetching from API...", current_year)
            await self.async_fetch_individual_year(current_year)

        # Preload next year's cache if we are in December
        if today.month == 12:
            next_year_store = self._get_store(current_year + 1)
            next_year_cache = await next_year_store.async_load()
            if next_year_cache:
                self.next_year_data = next_year_cache.get("records", [])
                _LOGGER.info("Preloaded next year's cached prayer times for %s", current_year + 1)

    async def async_fetch_individual_year(self, year: int) -> bool:
        """Scan the Collection to locate and cache a specific year's dataset."""
        collection_url = f"https://api-production.data.gov.sg/v2/public/api/collections/{self.collection_id}/metadata"
        _LOGGER.info("Scanning collection %s for year %s schedule...", self.collection_id, year)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(collection_url, timeout=15) as response:
                    if response.status != 200:
                        _LOGGER.error("Failed to fetch collection metadata, status: %s", response.status)
                        self.sync_status = "failed"
                        return False
                    
                    payload = await response.json()
                    child_datasets = payload.get("data", {}).get("collectionMetadata", {}).get("childDatasets", [])
                    
                    # 1. Loop through child datasets to find the target year
                    target_resource_id = None
                    for ds_id in child_datasets:
                        ds_meta_url = f"https://api-production.data.gov.sg/v2/public/api/datasets/{ds_id}/metadata"
                        async with session.get(ds_meta_url, timeout=10) as meta_res:
                            if meta_res.status != 200:
                                continue
                            meta_payload = await meta_res.json()
                            ds_name = meta_payload.get("data", {}).get("name", "")
                            
                            # Skip consolidated dataset
                            if "consolidated" in ds_name.lower():
                                continue
                            
                            # Check if the year matches the title
                            if str(year) in ds_name:
                                _LOGGER.info("Found matching dataset for %s: %s (%s)", year, ds_name, ds_id)
                                target_resource_id = ds_id
                                break
                    
                    if not target_resource_id:
                        _LOGGER.warning("Could not find dataset for year %s in collection %s", year, self.collection_id)
                        self.sync_status = "failed"
                        return False
                    
                    # 2. Download matching year's datastore records
                    datastore_url = f"https://data.gov.sg/api/action/datastore_search?resource_id={target_resource_id}&limit=400"
                    async with session.get(datastore_url, timeout=15) as ds_res:
                        if ds_res.status != 200:
                            _LOGGER.error("Failed to download datastore for resource %s", target_resource_id)
                            self.sync_status = "failed"
                            return False
                        
                        ds_payload = await ds_res.json()
                        if not ds_payload.get("success"):
                            _LOGGER.error("Datastore search returned unsuccessful: %s", ds_payload)
                            self.sync_status = "failed"
                            return False
                        
                        records = ds_payload.get("result", {}).get("records", [])
                        if not records:
                            _LOGGER.error("No records found in datastore response")
                            self.sync_status = "failed"
                            return False
                        
                        # 3. Cache the records locally
                        now_str = datetime.datetime.now().isoformat()
                        year_store = self._get_store(year)
                        await year_store.async_save({
                            "records": records,
                            "last_sync": now_str
                        })
                        
                        # Update current state if it matches active year
                        current_year = datetime.date.today().year
                        if year == current_year:
                            self.data = records
                            self.last_sync_success = now_str
                            self.sync_status = "success"
                        elif year == current_year + 1:
                            self.next_year_data = records
                            
                        _LOGGER.info("Successfully fetched and cached %s records for year %s", len(records), year)
                        return True
                        
        except Exception as err:
            _LOGGER.error("Error fetching and caching individual year %s: %s", year, err)
            self.sync_status = "failed"
            return False

    async def async_periodic_check(self, now_time):
        """Run periodic check to fetch current year data (if missing) and next year data (if in Nov/Dec and missing)."""
        today = datetime.date.today()
        current_year = today.year
        
        # 1. Retry current year's data if it is missing from memory
        if not self.data:
            _LOGGER.info("Current year schedule data is missing. Retrying fetch from data.gov.sg...")
            await self.async_fetch_individual_year(current_year)
            
        # 2. Fetch next year's data in November/December if missing (once a week)
        if today.month in [11, 12]:
            next_year = current_year + 1
            next_year_store = self._get_store(next_year)
            next_year_cache = await next_year_store.async_load()
            
            if not next_year_cache and not self.next_year_data:
                now = datetime.datetime.now()
                if (
                    self._last_next_year_check is None
                    or now - self._last_next_year_check > timedelta(days=7)
                ):
                    self._last_next_year_check = now
                    _LOGGER.info("It is %s but next year's schedule cache (%s) is missing. Checking API...", today.strftime("%B"), next_year)
                    success = await self.async_fetch_individual_year(next_year)
                    if success:
                        _LOGGER.info("Successfully fetched and cached next year's (%s) schedule!", next_year)
                    else:
                        _LOGGER.warning("Could not find next year's (%s) schedule on data.gov.sg yet. Will retry in a week.", next_year)

    def get_schedule_for_date(self, date_str: str):
        """Get the prayer schedule record for a specific date (YYYY-MM-DD)."""
        year = int(date_str.split("-")[0])
        current_year = datetime.date.today().year
        
        # Pick the active dataset array
        records = self.data if year == current_year else self.next_year_data
        
        for rec in records:
            if rec.get("Date") == date_str:
                return rec
        return None
