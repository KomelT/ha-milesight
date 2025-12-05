"""Binary sensors for Milesight devices."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, SIGNAL_DEVICE_UPDATED, SIGNAL_NEW_DEVICE
from .manager import MilesightManager, MilesightDevice
from .models import MODEL_BINARIES


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    manager: MilesightManager = hass.data[DOMAIN][entry.entry_id]

    @callback
    def _async_add_device(dev_eui: str) -> None:
        device = manager.get_device(dev_eui)
        if not device:
            return
        descriptions = MODEL_BINARIES.get(device.model)
        if not descriptions:
            return
        entities: list[MilesightBinarySensor] = []
        for description in descriptions:
            entities.append(
                MilesightBinarySensor(manager, device, description, entry.entry_id)
            )
        async_add_entities(entities)

    for dev_eui in list(manager.devices.keys()):
        _async_add_device(dev_eui)

    entry.async_on_unload(
        async_dispatcher_connect(
            hass, SIGNAL_NEW_DEVICE.format(entry_id=entry.entry_id), _async_add_device
        )
    )


class MilesightBinarySensor(BinarySensorEntity):
    """Binary sensor for Milesight telemetry."""

    _attr_should_poll = False

    def __init__(
        self,
        manager: MilesightManager,
        device: MilesightDevice,
        description: BinarySensorEntityDescription,
        entry_id: str,
    ) -> None:
        self.entity_description = description
        self._manager = manager
        self._dev_eui = device.dev_eui.lower()
        self._entry_id = entry_id
        self._attr_unique_id = f"{self._dev_eui}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._dev_eui)},
            manufacturer="Milesight",
            model=device.model,
            name=device.name or f"Milesight {self._dev_eui[-4:]}",
        )

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                SIGNAL_DEVICE_UPDATED.format(
                    entry_id=self._entry_id, dev_eui=self._dev_eui
                ),
                self._async_handle_update,
            )
        )
        self._async_handle_update(self._dev_eui)

    @callback
    def _async_handle_update(self, _dev_eui: str) -> None:
        device = self._manager.get_device(self._dev_eui)
        if not device:
            return
        value = device.telemetry.get(self.entity_description.key)
        self._attr_is_on = self._as_on(self.entity_description.key, value)
        self._attr_extra_state_attributes = {
            "last_seen": device.last_seen.isoformat()
        }
        self.async_write_ha_state()

    def _as_on(self, key: str, value) -> bool:
        """Map raw telemetry to boolean."""
        if value is None:
            return False
        if isinstance(value, str):
            value_norm = value.lower()
        else:
            value_norm = value

        if key == "window_detection":
            return value_norm in ("open", 1, True, "1")
        if key == "tamper_status":
            return value_norm in ("uninstalled", 1, True, "1")
        if key == "freeze_protection":
            return value_norm in ("triggered", 1, True, "1")
        if key == "motor_calibration_result":
            return value_norm not in ("success", 0, False, "0")

        return bool(value_norm)
