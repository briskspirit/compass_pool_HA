"""Compass WiFi Pool Heater integration for Home Assistant."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import CompassApi
from .const import DOMAIN
from .coordinator import CompassCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [
    Platform.CLIMATE,
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.NUMBER,
]

# Exact unique_id suffixes of entities removed since v1.0
_STALE_SUFFIXES = (
    "_compressor",    # text sensor, replaced by _compressor_running binary
    "_fault_detail",  # text sensor, replaced by _fault_status sensor
    "_fault",         # binary sensor, replaced by _fault_status sensor
    "_no_flow",       # binary sensor, merged into _fault_status sensor
    "_online",        # binary sensor, redundant with HA unavailable state
    "_lock",          # switch, removed for safety
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Compass Pool from a config entry."""
    session = async_get_clientsession(hass)
    api = CompassApi(
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
        session=session,
    )

    await api.login()
    devices = await api.get_devices()

    coordinators: dict[str, CompassCoordinator] = {}
    for device in devices:
        key = device["unique_key"]
        coordinator = CompassCoordinator(hass, api, key, device)
        await coordinator.async_config_entry_first_refresh()
        coordinators[key] = coordinator

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
        "coordinators": coordinators,
    }

    # Remove stale entities left over from previous integration versions
    ent_reg = er.async_get(hass)
    stale_unique_ids = set()
    for key in coordinators:
        for suffix in _STALE_SUFFIXES:
            stale_unique_ids.add(f"{key}{suffix}")
    for entity_entry in er.async_entries_for_config_entry(ent_reg, entry.entry_id):
        if entity_entry.unique_id in stale_unique_ids:
            _LOGGER.info("Removing stale entity: %s", entity_entry.entity_id)
            ent_reg.async_remove(entity_entry.entity_id)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
