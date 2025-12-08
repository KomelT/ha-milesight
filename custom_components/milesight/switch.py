"""Switch entities for Milesight devices (e.g., child lock)."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, SIGNAL_DEVICE_UPDATED, SIGNAL_NEW_DEVICE
from .manager import MilesightManager, MilesightDevice

_SUPPORTED_CHILD_LOCK_MODELS = {"WT101"}
_CHILD_LOCK_KEY = "child_lock_config.enable"


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    manager: MilesightManager = hass.data[DOMAIN][entry.entry_id]

    @callback
    def _async_add_device(dev_eui: str) -> None:
        device = manager.get_device(dev_eui)
        if not device or device.model.upper() not in _SUPPORTED_CHILD_LOCK_MODELS:
            return
        async_add_entities([MilesightChildLockSwitch(manager, device, entry.entry_id)])

    # Add existing devices (if any)
    for dev_eui in list(manager.devices.keys()):
        _async_add_device(dev_eui)

    entry.async_on_unload(
        async_dispatcher_connect(
            hass, SIGNAL_NEW_DEVICE.format(entry_id=entry.entry_id), _async_add_device
        )
    )


class MilesightChildLockSwitch(SwitchEntity):
    """Toggle child lock via downlink; reflect state from telemetry."""

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
        self._attr_unique_id = f"{self._dev_eui}_child_lock"
        self._attr_name = f"{device.name or 'Milesight'} Child Lock"
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
        value = self._extract_child_lock(device)
        self._attr_is_on = value
        self._attr_extra_state_attributes = {
            "last_seen": device.last_seen.isoformat(),
            "model": device.model,
        }
        self.async_write_ha_state()

    def _extract_child_lock(self, device: MilesightDevice) -> bool:
        """Read child lock state from telemetry."""
        value = None
        if isinstance(device.telemetry.get("child_lock_config"), dict):
            value = device.telemetry["child_lock_config"].get("enable")
        if value is None:
            value = device.telemetry.get(_CHILD_LOCK_KEY)
        return str(value).lower() in ("1", "on", "true", "enabled", "enable")

    async def async_turn_on(self, **kwargs) -> None:
        await self._send_child_lock(True)

    async def async_turn_off(self, **kwargs) -> None:
        await self._send_child_lock(False)

    async def _send_child_lock(self, enabled: bool) -> None:
        """Send downlink via existing service to change child lock."""
        dev = self._manager.get_device(self._dev_eui)
        if not dev:
            return
        payload = {"child_lock_config": {"enable": 1 if enabled else 0}}
        await self.hass.services.async_call(
            DOMAIN,
            "send_command",
            {"dev_eui": self._dev_eui, "model": dev.model.lower(), "payload": payload},
            blocking=True,
        )
        # Optimistic update; actual state will refresh on next uplink
        self._attr_is_on = enabled
        self.async_write_ha_state()
