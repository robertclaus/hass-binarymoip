"""Binary MoIP Receiver as a Media Player."""
import logging

from homeassistant.helpers.entity import Entity
from ..binarymoip import DEVICES

_LOGGER = logging.getLogger(__name__)

DEFAULT_DEVICE_CLASS = 'moip'
DEVICE_ID = 'pybinarymoip'
DEVICE_NAME = 'Binary MoIP Tx'

# ICON = 'mdi:television'


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the MoIP receivers as media_player devices."""
    devs = []
    for s in hass.data[DEVICES]['sensor']:
        hass_s = MoIP_Sensor_Tx(s)
        devs.append(hass_s)

    add_entities(devs, True)
    _LOGGER.debug("MoIP Tx Added %s", devs)
    return True


class MoIP_Sensor_Tx(Entity):
    """Sensor implementation for MoIP Transmitter."""

    def __init__(self, moip_tx):
        """Initialize MoIP Rx device."""
        self._tx = moip_tx
        self._unique_id = 'binarymoip-tx-{}-{}'.format(
            moip_tx.name, moip_tx.num)

#    @util.Throttle(MIN_TIME_BETWEEN_SCANS, MIN_TIME_BETWEEN_FORCED_SCANS)
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
