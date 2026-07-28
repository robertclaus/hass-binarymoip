"""Binary MoIP Transmitter as a Sensor."""
import logging

from homeassistant.helpers.entity import Entity
from .const import DEVICES

_LOGGER = logging.getLogger(__name__)

DEFAULT_DEVICE_CLASS = 'moip'
DEVICE_ID = 'pybinarymoip'
DEVICE_NAME = 'Binary MoIP Tx'


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the MoIP transmitters as sensor devices (configuration.yaml)."""
    devs = [MoIP_Sensor_Tx(s) for s in hass.data[DEVICES]['sensor']]
    add_entities(devs, True)
    _LOGGER.debug("MoIP Tx Added %s", devs)
    return True


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the MoIP transmitters as sensor devices (config entry)."""
    devs = [MoIP_Sensor_Tx(s) for s in hass.data[DEVICES]['sensor']]
    async_add_entities(devs, True)
    _LOGGER.debug("MoIP Tx Added %s", devs)


class MoIP_Sensor_Tx(Entity):
    """Sensor implementation for MoIP Transmitter."""

    def __init__(self, moip_tx):
        """Initialize MoIP Rx device."""
        self._tx = moip_tx
        self._unique_id = 'binarymoip-tx-{}-{}'.format(
            moip_tx.name, moip_tx.num)

    def update(self):
        """Retrieve latest state of the device."""
        pass

    @property
    def state(self):
        """Return the state of the device."""
        return self._tx.num

    @property
    def name(self):
        """Return the name of the device."""
        return "moip_tx_" + self._tx.name

    @property
    def should_poll(self):
        """Polling is needed."""
        return False

    @property
    def unique_id(self):
        """Unique ID of the transmitter. TODO make this better."""
        return self._unique_id
