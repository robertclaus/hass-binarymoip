"""Binary MoIP Receiver IR output as a Remote."""
import logging

from homeassistant.components.remote import RemoteEntity

from .const import DEVICES, power_on_key, power_off_key

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the MoIP receivers' IR outputs as remote entities (configuration.yaml)."""
    devs = [MoIP_Remote_Rx(mp) for mp in hass.data[DEVICES]['remote']]
    add_entities(devs, True)
    _LOGGER.debug("MoIP Remote Added %s", devs)
    return True


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the MoIP receivers' IR outputs as remote entities (config entry)."""
    devs = [
        MoIP_Remote_Rx(
            mp,
            entry.options.get(power_on_key(mp.name)),
            entry.options.get(power_off_key(mp.name)),
        )
        for mp in hass.data[DEVICES]['remote']
    ]
    async_add_entities(devs, True)
    _LOGGER.debug("MoIP Remote Added %s", devs)


class MoIP_Remote_Rx(RemoteEntity):
    """Remote implementation for a MoIP Receiver's IR flasher output.

    send_command takes one or more Pronto Hex strings and fires them out
    the receiver's IR port -- useful for testing or one-off commands.
    turn_on/turn_off send whichever power code was configured for this
    receiver in the integration's options (Settings > Devices & Services >
    Binary MoIP > Configure). There's no feedback path from the IR flasher,
    so is_on just tracks the last requested state rather than anything the
    receiver actually confirms.
    """

    def __init__(self, moip_rx, power_on_code=None, power_off_code=None):
        """Initialize MoIP Rx IR remote."""
        self._rx = moip_rx
        self._is_on = True
        self._power_on_code = power_on_code
        self._power_off_code = power_off_code
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
        """Send this receiver's configured power-on IR code, if any.

        Falls back to the power-off code if only that one is configured,
        since some TVs only have a single power-toggle code rather than
        discrete on/off codes.
        """
        code = self._power_on_code or self._power_off_code
        if code:
            self._rx.send_ir(code.strip())
        self._is_on = True

    def turn_off(self, **kwargs):
        """Send this receiver's configured power-off IR code, if any.

        Falls back to the power-on code if only that one is configured,
        since some TVs only have a single power-toggle code rather than
        discrete on/off codes.
        """
        code = self._power_off_code or self._power_on_code
        if code:
            self._rx.send_ir(code.strip())
        self._is_on = False

    def send_command(self, command, **kwargs):
        """Send one or more IR commands (Pronto Hex strings) to this receiver."""
        num_repeats = kwargs.get("num_repeats", 1)
        for _ in range(num_repeats):
            for code in command:
                self._rx.send_ir(code.strip())
