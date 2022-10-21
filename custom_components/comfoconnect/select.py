"""Manage a Zehnder ComfoAir Bypass"""
from pycomfoconnect import (
	CMD_BYPASS_AUTO,
	CMD_BYPASS_ON,
	CMD_BYPASS_OFF,
    SENSOR_BYPASS_ACTIVATIONSTATE
)

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.util.percentage import (
    int_states_in_range,
    percentage_to_ranged_value,
    ranged_value_to_percentage,
)

from . import DOMAIN, SIGNAL_COMFOCONNECT_UPDATE_RECEIVED, ComfoConnectBridge
import logging

_LOGGER = logging.getLogger(__name__)

CMD_MAPPING = {
    "auto": CMD_BYPASS_AUTO,
    "on": CMD_BYPASS_ON,
    "off": CMD_BYPASS_OFF
}

MODE_MAPPING = { 0: "auto", 1: "on", 2: "off"}



def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the ComfoConnect bypass."""
    ccb = hass.data[DOMAIN]

    add_entities([ComfoConnectByPass(ccb)], True)


class ComfoConnectByPass(SelectEntity):
    """Representation of the ComfoConnect bypass."""

    _attr_icon = "mdi:air-conditioner"
    _attr_should_poll = False
    _attr_options = ['auto', 'on', 'off']
    current_mode = None

    def __init__(self, ccb: ComfoConnectBridge) -> None:
        """Initialize the ComfoConnect bypass."""
        self._ccb = ccb
        self._attr_name = ccb.name + "bypass"
        self._attr_unique_id = ccb.unique_id

    async def async_added_to_hass(self) -> None:
        """Register for sensor updates."""
        _LOGGER.debug("Registering for bypass activation state")
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                SIGNAL_COMFOCONNECT_UPDATE_RECEIVED.format(SENSOR_BYPASS_ACTIVATIONSTATE),
                self._handle_update,
            )
        )
        await self.hass.async_add_executor_job(
            self._ccb.comfoconnect.register_sensor, SENSOR_BYPASS_ACTIVATIONSTATE
        )

    def _handle_update(self, value: float) -> None:
        """Handle update callbacks."""
        _LOGGER.debug(
            "Handle update for bypass activation state(%d): %s", SENSOR_BYPASS_ACTIVATIONSTATE, value
        )
        self.current_mode = MODE_MAPPING[value]
        self.schedule_update_ha_state()

    @property
    def state(self):
        """Return  the current option"""
        return self.current_mode

    def select_option(self, mode: str) -> None:
        """Set bypass mode."""
        _LOGGER.debug("Changing bypass mode to %s", mode)

        cmd = CMD_MAPPING[mode]
        self._ccb.comfoconnect.cmd_rmi_request(cmd)
