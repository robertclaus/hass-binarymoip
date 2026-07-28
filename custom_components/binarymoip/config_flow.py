"""Config flow for the Binary MoIP integration."""
import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_USERNAME, CONF_PASSWORD
from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN, power_on_key, power_off_key

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

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler()


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Per-receiver IR power code configuration.

    Pronto Hex codes are TV-specific, so they can't be baked into the
    integration -- the user supplies them per receiver here. Leaving both
    fields blank for a receiver just means its remote's turn_on/turn_off
    won't send anything.
    """

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        moip = self.hass.data.get(DOMAIN, {}).get(self.config_entry.entry_id)
        receivers = moip.receivers if moip else []

        schema_dict = {}
        for rx in receivers:
            on_key = power_on_key(rx.name)
            off_key = power_off_key(rx.name)
            schema_dict[vol.Optional(
                on_key,
                description={
                    "suggested_value": self.config_entry.options.get(on_key, "")},
            )] = str
            schema_dict[vol.Optional(
                off_key,
                description={
                    "suggested_value": self.config_entry.options.get(off_key, "")},
            )] = str

        return self.async_show_form(
            step_id="init", data_schema=vol.Schema(schema_dict)
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
