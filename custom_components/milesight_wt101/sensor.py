"""Sensor entities for Milesight WT101."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, SIGNAL_DEVICE_UPDATED, SIGNAL_NEW_DEVICE
from .manager import MilesightManager, MilesightDevice


SENSOR_DESCRIPTIONS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="battery",
        name="Battery",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
    ),
    SensorEntityDescription(
        key="temperature",
        name="Ambient Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
    ),
    SensorEntityDescription(
        key="target_temperature",
        name="Target Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
    ),
    SensorEntityDescription(
        key="valve_opening",
        name="Valve Opening",
        native_unit_of_measurement=PERCENTAGE,
    ),
    SensorEntityDescription(
        key="tamper_status",
        name="Installation Status",
    ),
    SensorEntityDescription(
        key="window_detection",
        name="Open Window Detection",
    ),
    SensorEntityDescription(
        key="motor_calibration_result",
        name="Motor Calibration Result",
    ),
    SensorEntityDescription(
        key="motor_stroke",
        name="Motor Stroke",
    ),
    SensorEntityDescription(
        key="freeze_protection",
        name="Freeze Protection",
    ),
    SensorEntityDescription(
        key="motor_position",
        name="Motor Position",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    manager: MilesightManager = hass.data[DOMAIN][entry.entry_id]

    @callback
    def _async_add_device(dev_eui: str) -> None:
        device = manager.get_device(dev_eui)
        if not device:
            return
        new_entities: list[MilesightSensor] = []
        for description in SENSOR_DESCRIPTIONS:
            new_entities.append(
                MilesightSensor(manager, device, description, entry.entry_id)
            )
        async_add_entities(new_entities)

    # Add existing devices (if any)
    for dev_eui in list(manager.devices.keys()):
        _async_add_device(dev_eui)

    # Listen for new devices
    entry.async_on_unload(
        async_dispatcher_connect(
            hass, SIGNAL_NEW_DEVICE.format(entry_id=entry.entry_id), _async_add_device
        )
    )


class MilesightSensor(SensorEntity):
    """Represents a single WT101 data point."""

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
            manufacturer="Milesight",
            model=device.model.upper(),
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
        self._attr_native_value = device.telemetry.get(self.entity_description.key)
        self._attr_extra_state_attributes = {
            "last_seen": device.last_seen.isoformat()
        }
        self.async_write_ha_state()
