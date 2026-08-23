"""Test the SG Muslim Prayer Timetable from MUIS config flow."""
import pytest
from unittest.mock import patch
from homeassistant import config_entries, data_entry_flow
from homeassistant.core import HomeAssistant

from custom_components.sg_muslim_prayer_timetable_from_muis.const import DOMAIN, CONF_COLLECTION_ID

@pytest.mark.asyncio
async def test_config_flow_user_step(hass: HomeAssistant) -> None:
    """Test user step in config flow."""
    # 1. Initialize config flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    
    # Verify it displays a form for the user step
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "user"
    
    # 2. Submit the form with collection ID
    with patch(
        "custom_components.sg_muslim_prayer_timetable_from_muis.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_COLLECTION_ID: "2312"},
        )
        await hass.async_block_till_done()

    # Verify it successfully creates the entry
    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["title"] == "SG Muslim Prayer Timetable from MUIS"
    assert result["data"] == {
        CONF_COLLECTION_ID: "2312",
    }
    assert len(mock_setup_entry.mock_calls) == 1
