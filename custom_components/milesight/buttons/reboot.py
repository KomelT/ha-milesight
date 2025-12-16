"""Reboot button entity."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.entity import DeviceInfo, EntityCategory

from ..const import DOMAIN
from ..manager import MilesightManager, MilesightDevice


class MilesightRebootButton(ButtonEntity):
    """Send a reboot downlink."""

    _attr_should_poll = False
    _attr_entity_registry_enabled_default = True
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:restart"

    def __init__(
        self,
        manager: MilesightManager,
        device: MilesightDevice,
        entry_id: str,
    ) -> None:
        self._manager = manager
        self._dev_eui = device.dev_eui.lower()
        self._entry_id = entry_id
        self._attr_unique_id = f"{self._entry_id}_{self._dev_eui}_reboot"
        self._attr_name = "Reboot"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._dev_eui)},
        )

    async def async_press(self) -> None:
        """Publish a reboot command via the existing service."""
        dev = self._manager.get_device(self._dev_eui)
        if not dev:
            return
        payload = {"reboot": 1}
        await self.hass.services.async_call(
            DOMAIN,
            "send_command",
            {"dev_eui": self._dev_eui, "model": dev.model.lower(), "payload": payload},
            blocking=True,
        )
