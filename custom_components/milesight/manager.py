from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Dict, Optional

from homeassistant.components import mqtt
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import DOMAIN, SIGNAL_DEVICE_UPDATED, SIGNAL_NEW_DEVICE

_LOGGER = logging.getLogger(__name__)


@dataclass
class MilesightDevice:
    dev_eui: str
    model: str
    name: Optional[str] = None
    serial_number: Optional[str] = None
    sw_version: Optional[str] = None
    hw_version: Optional[str] = None
    last_seen: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    telemetry: Dict[str, object] = field(default_factory=dict)


class MilesightManager:
    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        self.hass = hass
        self.entry_id = entry_id
        self.devices: Dict[str, MilesightDevice] = {}
        self._unsubscribers: list[Callable[[], None]] = []

    async def async_close(self) -> None:
        while self._unsubscribers:
            unsub = self._unsubscribers.pop()
            unsub()

    def get_device(self, dev_eui: str) -> Optional[MilesightDevice]:
        return self.devices.get(dev_eui)

    def register_mqtt(self, unsub: Callable[[], None]) -> None:
        self._unsubscribers.append(unsub)

    async def async_handle_join_uplink(self, msg: mqtt.ReceiveMessage) -> None:
        topic_dev_eui, topic_model = self._parse_topic(msg.topic)

        parsed = {}

        try:
            parsed = json.loads(msg.payload)
        except json.JSONDecodeError:
            parsed = None

        if not parsed:
            _LOGGER.warning("Ignoring unparsable uplink: %s", msg.payload)
            return

        await self._async_add_or_update_device(
            topic_dev_eui,
            model=topic_model,
            data=parsed,
        )

    async def _async_add_or_update_device(
        self,
        dev_eui: str,
        model: Optional[str] = None,
        data: Optional[Dict[str, object]] = None,
    ) -> None:
        if dev_eui is None:
            _LOGGER.warning("Skipping device update with missing dev_eui")
            return

        dev_eui = dev_eui.lower().strip()
        if not dev_eui:
            _LOGGER.warning("Skipping device update with missing dev_eui")
            return

        name = data.get("deviceName")

        model = model.upper() if model else data.get("model", "UNKNOWN").upper()

        device = self.devices.get(dev_eui)

        if not device:
            device = MilesightDevice(
                dev_eui=dev_eui,
                name=name if name else f"Milesight {dev_eui[-4:]}",
                model=model,
            )
            self.devices[dev_eui] = device
            async_dispatcher_send(
                self.hass, SIGNAL_NEW_DEVICE.format(entry_id=self.entry_id), dev_eui
            )

        device.last_seen = datetime.now(timezone.utc)
        serial_number = data.get("sn")
        firmware_version = data.get("firmware_version")
        hardware_version = data.get("hardware_version")

        if name:
            device.name = name
        if model:
            device.model = model
        if serial_number:
            device.serial_number = serial_number
        if firmware_version:
            device.sw_version = firmware_version
        if hardware_version:
            device.hw_version = hardware_version
        if data:
            for key, value in data.items():
                if key in ("deviceName", "model"):
                    continue
                device.telemetry[key] = value

        await self._async_sync_device_registry(device)
        async_dispatcher_send(
            self.hass,
            SIGNAL_DEVICE_UPDATED.format(entry_id=self.entry_id, dev_eui=dev_eui),
            dev_eui,
        )

    async def _async_sync_device_registry(self, dev: MilesightDevice) -> None:
        """Ensure device is represented in HA's registry."""
        registry = dr.async_get(self.hass)
        registry.async_get_or_create(
            config_entry_id=self.entry_id,
            identifiers={(DOMAIN, dev.dev_eui.lower())},
            manufacturer="Milesight",
            name=dev.name or f"Milesight {dev.dev_eui[-4:]}",
            model=dev.model.upper(),
            sw_version=dev.sw_version,
            hw_version=dev.hw_version,
            serial_number=dev.serial_number,
        )

    def _parse_topic(self, topic: str | None) -> tuple[Optional[str], Optional[str]]:
        """Extract dev_eui and model from topic milesight/{model}/{dev_eui}/<type>."""
        if not topic:
            return None, None
        parts = topic.split("/")
        if len(parts) < 4 or parts[0] != "milesight":
            return None, None
        model = parts[1].upper() if parts[1] else None
        dev_eui = parts[2]
        return dev_eui, model
