"""Binary MoIP Receiver IR output as a Remote."""
import logging

from homeassistant.components.remote import RemoteEntity

from .const import DEVICES

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the MoIP receivers' IR outputs as remote entities (configuration.yaml)."""
    devs = [MoIP_Remote_Rx(mp) for mp in hass.data[DEVICES]['remote']]
    add_entities(devs, True)
    _LOGGER.debug("MoIP Remote Added %s", devs)
    return True


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the MoIP receivers' IR outputs as remote entities (config entry)."""
    devs = [MoIP_Remote_Rx(mp) for mp in hass.data[DEVICES]['remote']]
    async_add_entities(devs, True)
    _LOGGER.debug("MoIP Remote Added %s", devs)


class MoIP_Remote_Rx(RemoteEntity):
    """Remote implementation for a MoIP Receiver's IR flasher output.

    This is a raw IR blaster: send_command takes one or more Pronto Hex
    strings and fires them out the receiver's IR port. There's no feedback
    path from the IR flasher, so is_on just tracks the last requested state
    rather than anything the receiver actually confirms.
    """

    def __init__(self, moip_rx):
        """Initialize MoIP Rx IR remote."""
        self._rx = moip_rx
        self._is_on = True
        self._unique_id = 'binarymoip-remote-{}-{}'.format(
            moip_rx.name, moip_rx.num)

    @property
    def name(self):
        """Return the name of the device."""
        return "moip_rx_" + self._rx.name + "_ir"

    @property
    def should_poll(self):
        """No state to refresh from the device."""
        return False

    @property
    def is_on(self):
        """Return the last requested on/off state (no feedback from the IR port)."""
        return self._is_on

    @property
    def unique_id(self):
        """Unique ID of this remote."""
        return self._unique_id

    def turn_on(self, **kwargs):
        """Mark the remote as on. No IR is sent without a configured command."""
        self._is_on = True

    def turn_off(self, **kwargs):
        """Mark the remote as off. No IR is sent without a configured command."""
        self._is_on = False

    def send_command(self, command, **kwargs):
        """Send one or more IR commands (Pronto Hex strings) to this receiver."""
        num_repeats = kwargs.get("num_repeats", 1)
        for _ in range(num_repeats):
            for code in command:
                self._rx.send_ir(code.strip())
