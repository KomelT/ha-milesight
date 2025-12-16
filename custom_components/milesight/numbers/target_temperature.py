"""Target temperature number entity."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity
from homeassistant.const import UnitOfTemperature
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo

from ..const import DOMAIN, SIGNAL_DEVICE_UPDATED
from ..manager import MilesightManager, MilesightDevice


class MilesightTargetTempNumber(NumberEntity):
    """Set target temperature via downlink; reflect from telemetry."""

    _attr_should_poll = False
    _attr_entity_registry_enabled_default = True
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_native_min_value = 10
    _attr_native_max_value = 28
    _attr_native_step = 1

    def __init__(
        self,
        manager: MilesightManager,
        device: MilesightDevice,
        entry_id: str,
    ) -> None:
        self._manager = manager
        self._dev_eui = device.dev_eui.lower()
        self._entry_id = entry_id
        self._attr_unique_id = f"{self._entry_id}_{self._dev_eui}_target_temperature"
        self._attr_name = "Target Temperature"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, self._dev_eui)})

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
        self._attr_native_value = device.telemetry.get("target_temperature")
        self._attr_extra_state_attributes = {
            "last_seen": device.last_seen.isoformat(),
            "model": device.model,
        }
        self.async_write_ha_state()

    async def async_set_native_value(self, value: float) -> None:
        """Send downlink to set target temperature."""
        dev = self._manager.get_device(self._dev_eui)
        if not dev:
            return
        # WT101 encoder expects temperature_tolerance; default to 0 when not set.
        payload = {"target_temperature": float(value), "temperature_tolerance": 1}
        await self.hass.services.async_call(
            DOMAIN,
            "send_command",
            {"dev_eui": self._dev_eui, "model": dev.model.lower(), "payload": payload},
            blocking=True,
        )
        self._attr_native_value = float(value)
        self.async_write_ha_state()
