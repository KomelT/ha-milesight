"""Number entities for Milesight devices (delegates to per-number modules)."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, SIGNAL_NEW_DEVICE
from .manager import MilesightManager
from .numbers import MilesightTargetTempNumber

_SUPPORTED_TARGET_TEMP_MODELS = {"WT101"}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    manager: MilesightManager = hass.data[DOMAIN][entry.entry_id]

    @callback
    def _async_add_device(dev_eui: str) -> None:
        device = manager.get_device(dev_eui)
        if not device:
            return
        entities = []
        if device.model.upper() in _SUPPORTED_TARGET_TEMP_MODELS:
            entities.append(MilesightTargetTempNumber(manager, device, entry.entry_id))
        if entities:
            async_add_entities(entities)

    for dev_eui in list(manager.devices.keys()):
        _async_add_device(dev_eui)

    entry.async_on_unload(
        async_dispatcher_connect(
            hass, SIGNAL_NEW_DEVICE.format(entry_id=entry.entry_id), _async_add_device
        )
    )
