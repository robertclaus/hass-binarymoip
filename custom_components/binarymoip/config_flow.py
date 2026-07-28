"""Config flow for the Binary MoIP integration."""
import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_USERNAME, CONF_PASSWORD
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_USERNAME, default="binary"): str,
        vol.Optional(CONF_PASSWORD, default="binary"): str,
    }
)


def _validate_connection(host, username, password):
    """Attempt to connect to the MoIP controller. Runs in an executor."""
    from .moip import MoIP

    moip = MoIP(host, username, password)
    moip.connect()
    if not moip.receivers and not moip.transmitters:
        raise CannotConnect
    return {
        "receivers": len(moip.receivers),
        "transmitters": len(moip.transmitters),
    }


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Binary MoIP."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_HOST])
            self._abort_if_unique_id_configured()

            try:
                info = await self.hass.async_add_executor_job(
                    _validate_connection,
                    user_input[CONF_HOST],
                    user_input.get(CONF_USERNAME),
                    user_input.get(CONF_PASSWORD),
                )
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                title = "Binary MoIP ({} TX, {} RX)".format(
                    info["transmitters"], info["receivers"])
                return self.async_create_entry(title=title, data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
