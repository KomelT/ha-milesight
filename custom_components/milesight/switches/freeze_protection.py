"""Freeze protection switch entity."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo

from ..const import DOMAIN, SIGNAL_DEVICE_UPDATED
from ..manager import MilesightManager, MilesightDevice

_FREEZE_PROTECTION_KEY = "freeze_protection"


class MilesightFreezeProtectionSwitch(SwitchEntity):
    _attr_should_poll = False
    _attr_entity_registry_enabled_default = True

    def __init__(
        self,
        manager: MilesightManager,
        device: MilesightDevice,
        entry_id: str,
    ) -> None:
        self._manager = manager
        self._dev_eui = device.dev_eui.lower()
        self._entry_id = entry_id
        self._attr_unique_id = f"{self._entry_id}_{self._dev_eui}_freeze_protection"
        self._attr_name = "Freeze Protection"
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
        value = self._extract_state(device)
        self._attr_is_on = value
        self._attr_extra_state_attributes = {
            "last_seen": device.last_seen.isoformat(),
            "model": device.model,
        }
        self.async_write_ha_state()

    def _extract_state(self, device: MilesightDevice) -> bool:
        value = device.telemetry.get(_FREEZE_PROTECTION_KEY)
        return str(value).lower() in ("1", "on", "true", "enabled", "enable")

    async def async_turn_on(self, **kwargs) -> None:
        await self._send_state(True)

    async def async_turn_off(self, **kwargs) -> None:
        await self._send_state(False)

    async def _send_state(self, enabled: bool) -> None:
        dev = self._manager.get_device(self._dev_eui)
        if not dev:
            return
        payload = {"freeze_protection_config": {"enable": 1 if enabled else 0}}
        await self.hass.services.async_call(
            DOMAIN,
            "send_command",
            {"dev_eui": self._dev_eui, "model": dev.model.lower(), "payload": payload},
            blocking=True,
        )
        self._attr_is_on = enabled
        self.async_write_ha_state()
