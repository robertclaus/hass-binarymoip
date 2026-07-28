"""Binary MoIP Receiver on-screen text as a Notify entity."""
import logging

from homeassistant.components.notify import NotifyEntity

from .const import DEVICES

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the MoIP receivers' on-screen text as notify entities (configuration.yaml)."""
    devs = [MoIP_Notify_Rx(mp) for mp in hass.data[DEVICES]['notify']]
    add_entities(devs)
    _LOGGER.debug("MoIP Notify Added %s", devs)
    return True


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the MoIP receivers' on-screen text as notify entities (config entry)."""
    devs = [MoIP_Notify_Rx(mp) for mp in hass.data[DEVICES]['notify']]
    async_add_entities(devs)
    _LOGGER.debug("MoIP Notify Added %s", devs)


class MoIP_Notify_Rx(NotifyEntity):
    """Notify implementation that overlays text on a MoIP Receiver's video output.

    This is a direct mapping to the !OSD protocol command: no history, no
    delivery confirmation beyond the controller's OK/#Error response. Send
    message="CLEAR" to remove whatever is currently shown.
    """

    def __init__(self, moip_rx):
        """Initialize MoIP Rx OSD notify entity."""
        self._rx = moip_rx
        self._attr_unique_id = 'binarymoip-notify-{}-{}'.format(
            moip_rx.name, moip_rx.num)

    @property
    def name(self):
        """Return the name of the device."""
        return "moip_rx_" + self._rx.name + "_osd"

    @property
    def should_poll(self):
        """No state to refresh from the device."""
        return False

    async def async_send_message(self, message, title=None):
        """Show a plain-text message overlaid on this receiver's video output."""
        await self.hass.async_add_executor_job(self._rx.show_osd_message, message)
