"""Sensor entities for Milesight devices."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, SIGNAL_DEVICE_UPDATED, SIGNAL_NEW_DEVICE
from .manager import MilesightManager, MilesightDevice
from .models import MODEL_SENSORS


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    manager: MilesightManager = hass.data[DOMAIN][entry.entry_id]

    @callback
    def _async_add_device(dev_eui: str) -> None:
        device = manager.get_device(dev_eui)
        if not device:
            return
        descriptions = MODEL_SENSORS.get(device.model.upper())
        if not descriptions:
            return
        new_entities: list[MilesightSensor] = []
        for description in descriptions:
            new_entities.append(
                MilesightSensor(manager, device, description, entry.entry_id)
            )
        async_add_entities(new_entities)

    # Add existing devices (if any)
    for dev_eui in list(manager.devices.keys()):
        _async_add_device(dev_eui)

    entry.async_on_unload(
        async_dispatcher_connect(
            hass, SIGNAL_NEW_DEVICE.format(entry_id=entry.entry_id), _async_add_device
        )
    )


class MilesightSensor(SensorEntity):
    """Represents a single Milesight datapoint."""

    _attr_should_poll = False
    _attr_entity_registry_enabled_default = True

    def __init__(
        self,
        manager: MilesightManager,
        device: MilesightDevice,
        description: SensorEntityDescription,
        entry_id: str,
    ) -> None:
        self.entity_description = description
        self._manager = manager
        self._dev_eui = device.dev_eui.lower()
        self._entry_id = entry_id
        self._attr_unique_id = f"{self._dev_eui}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._dev_eui)},
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
        if self.entity_description.key == "lorawan_class":
            # Map class index to friendly label, fall back to raw if unknown.
            mapping = {
                "0": "Class A",
                "1": "Class B",
                "2": "Class C",
                "3": "Class CtoB",
                0: "Class A",
                1: "Class B",
                2: "Class C",
                3: "Class CtoB",
            }
            value = mapping.get(value, value)
        elif self.entity_description.key == "motor_calibration_result":
            mapping = {
                "0": "success",
                "1": "fail: out of range",
                "2": "fail: uninstalled",
                "3": "calibration cleared",
                "4": "temperature control disabled",
                0: "success",
                1: "fail: out of range",
                2: "fail: uninstalled",
                3: "calibration cleared",
                4: "temperature control disabled",
            }
            value = mapping.get(value, value)
        self._attr_native_value = value
        self._attr_extra_state_attributes = {
            "last_seen": device.last_seen.isoformat(),
            "model": device.model,
        }
        self.async_write_ha_state()
