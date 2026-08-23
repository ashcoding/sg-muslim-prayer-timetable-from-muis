import voluptuous as vol
from homeassistant import config_entries
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN, DEFAULT_COLLECTION_ID, CONF_COLLECTION_ID

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SG Muslim Prayer Timetable from MUIS."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            return self.async_create_entry(
                title="SG Muslim Prayer Timetable from MUIS",
                data=user_input
            )

        data_schema = vol.Schema({
            vol.Required(CONF_COLLECTION_ID, default=DEFAULT_COLLECTION_ID): cv.string,
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors
        )
