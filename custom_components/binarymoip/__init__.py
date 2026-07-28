"""
Component for interacting with a SnapAV Binary-Brand Media Over IP
(MoIP) system for video distribution.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/binarymoip/
"""
from datetime import timedelta
import logging

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.const import (CONF_HOST, CONF_USERNAME,
                                  CONF_PASSWORD, CONF_SCAN_INTERVAL, Platform)
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import discovery

from .const import DOMAIN, DEVICES

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.MEDIA_PLAYER, Platform.SENSOR, Platform.REMOTE, Platform.NOTIFY]

# TODO: Make CONF_SCAN_INTERVAL do something
SCAN_INTERVAL = timedelta(seconds=120)

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_HOST): cv.string,
        vol.Optional(CONF_USERNAME): cv.string,
        vol.Optional(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_SCAN_INTERVAL, default=SCAN_INTERVAL): cv.time_period,
    })
}, extra=vol.ALLOW_EXTRA)


def _connect(host, username, password):
    """Connect to the MoIP controller. Performs blocking socket I/O."""
    from .moip import MoIP

    m = MoIP(host, username, password)
    m.connect()
    return m


def setup(hass, config):
    """Set up the Binary MoIP component from configuration.yaml."""
    if DOMAIN not in config:
        return True

    hass.data[DEVICES] = {'media_player': [],
                           'sensor': [],
                           'remote': [],
                           'notify': []}

    moip_config = config[DOMAIN]
    host = moip_config[CONF_HOST]
    username = moip_config.get(CONF_USERNAME)
    password = moip_config.get(CONF_PASSWORD)

    m = None
    try:
        m = _connect(host, username, password)
        for mp in m.receivers:
            _LOGGER.info("adding MoIP Rx %s", mp)
            hass.data[DEVICES]['media_player'].append(mp)
            hass.data[DEVICES]['remote'].append(mp)
            hass.data[DEVICES]['notify'].append(mp)
        for s in m.transmitters:
            _LOGGER.info("adding MoIP Tx %s", s)
            hass.data[DEVICES]['sensor'].append(s)
    except Exception as e:
        _LOGGER.error("Could not setup MoIP at %s - %s", host, e)

    hass.data[DOMAIN] = m

    discovery.load_platform(hass, 'media_player', DOMAIN, None, config)
    discovery.load_platform(hass, 'sensor', DOMAIN, None, config)
    discovery.load_platform(hass, 'remote', DOMAIN, None, config)
    discovery.load_platform(hass, 'notify', DOMAIN, None, config)

    return True


async def async_setup_entry(hass, entry):
    """Set up Binary MoIP from a config entry (added via the UI)."""
    host = entry.data[CONF_HOST]
    username = entry.data.get(CONF_USERNAME)
    password = entry.data.get(CONF_PASSWORD)

    m = await hass.async_add_executor_job(_connect, host, username, password)

    if not m.receivers and not m.transmitters:
        raise ConfigEntryNotReady(
            "Could not connect to Binary MoIP controller at %s" % host)

    hass.data[DEVICES] = {
        'media_player': list(m.receivers),
        'sensor': list(m.transmitters),
        'remote': list(m.receivers),
        'notify': list(m.receivers),
    }
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = m

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass, entry):
    """Unload a Binary MoIP config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
