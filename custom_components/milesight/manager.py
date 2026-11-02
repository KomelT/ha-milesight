from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Dict, Optional

from homeassistant.components import mqtt
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.exceptions import HomeAssistantError
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
    def __init__(
        self,
        hass: HomeAssistant,
        entry_id: str,
        uplink_topic: str,
        join_topic: str | None = None,
    ) -> None:
        self.hass = hass
        self.entry_id = entry_id
        self.devices: Dict[str, MilesightDevice] = {}
        self._unsubscribers: list[Callable[[], None]] = []
        self.uplink_topic = uplink_topic
        self.join_topic = join_topic or uplink_topic

    async def async_close(self) -> None:
        while self._unsubscribers:
            unsub = self._unsubscribers.pop()
            unsub()

    def get_device(self, dev_eui: str) -> Optional[MilesightDevice]:
        return self.devices.get((dev_eui or "").strip().lower())

    def register_mqtt(self, unsub: Callable[[], None]) -> None:
        self._unsubscribers.append(unsub)

    async def async_handle_join_uplink(
        self, msg: mqtt.ReceiveMessage, topic_filter: str | None = None
    ) -> None:
        topic_dev_eui, topic_model = self._parse_topic(
            msg.topic, topic_filter or self.uplink_topic
        )
        if not topic_dev_eui or not topic_model:
            _LOGGER.warning("Ignoring uplink with invalid topic: %s", msg.topic)
            return

        try:
            parsed = json.loads(msg.payload)
        except (json.JSONDecodeError, UnicodeDecodeError, TypeError):
            _LOGGER.warning("Ignoring unparsable uplink: %s", msg.payload)
            return
        if not isinstance(parsed, dict):
            _LOGGER.warning("Ignoring uplink that is not a JSON object")
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
        try:
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
        except HomeAssistantError as err:
            _LOGGER.warning(
                "Skipping device registry sync for %s: %s", dev.dev_eui, err
            )

    def _parse_topic(
        self, topic: str | None, topic_filter: str | None = None
    ) -> tuple[Optional[str], Optional[str]]:
        """Extract model and DevEUI using the configured subscription filter."""
        if not topic:
            return None, None
        parts = topic.split("/")
        pattern = (topic_filter or self.uplink_topic).split("/")
        if len(parts) != len(pattern):
            return None, None
        if any(expected not in ("+", actual) for actual, expected in zip(parts, pattern)):
            return None, None
        wildcard_positions = [
            index for index, expected in enumerate(pattern) if expected == "+"
        ]
        if len(wildcard_positions) != 2:
            return None, None
        model = parts[wildcard_positions[0]].strip()
        dev_eui = parts[wildcard_positions[1]].strip()
        if (
            not model
            or not dev_eui
            or dev_eui in ("+", "#")
            or model.lower() in {"unknown", "none", "null"}
        ):
            return None, None
        return dev_eui, model.upper()

    def serialize_devices(self) -> list[dict[str, object]]:
        """Return JSON-safe device data."""
        return [
            {
                "dev_eui": device.dev_eui,
                "model": device.model,
                "name": device.name,
                "serial_number": device.serial_number,
                "sw_version": device.sw_version,
                "hw_version": device.hw_version,
                "last_seen": device.last_seen.isoformat(),
                "telemetry": device.telemetry,
            }
            for device in self.devices.values()
        ]

    async def async_delete_device(self, dev_eui: str) -> bool:
        """Delete an in-memory device and its registry records."""
        key = (dev_eui or "").strip().lower()
        if not key or key not in self.devices:
            return False
        del self.devices[key]
        entity_registry = er.async_get(self.hass)
        for entity in list(entity_registry.entities.values()):
            if entity.config_entry_id == self.entry_id and entity.device_id:
                device = dr.async_get(self.hass).async_get(entity.device_id)
                if device and (DOMAIN, key) in device.identifiers:
                    entity_registry.async_remove(entity.entity_id)
        device_registry = dr.async_get(self.hass)
        device = device_registry.async_get_device(identifiers={(DOMAIN, key)})
        if device:
            device_registry.async_remove_device(device.id)
        return True
