"""State manager for Milesight devices."""

from __future__ import annotations

import base64
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Dict, Optional

from homeassistant.components import mqtt
from homeassistant.const import ATTR_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import DOMAIN, SIGNAL_DEVICE_UPDATED, SIGNAL_NEW_DEVICE
from .decoder import DecodeError, decode_payload

_LOGGER = logging.getLogger(__name__)


@dataclass
class MilesightDevice:
    """Simple in-memory model for a device."""

    dev_eui: str
    model: str
    name: Optional[str] = None
    last_seen: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    telemetry: Dict[str, object] = field(default_factory=dict)
    attributes: Dict[str, object] = field(default_factory=dict)


class MilesightManager:
    """Keep track of devices and push updates to HA."""

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        self.hass = hass
        self.entry_id = entry_id
        self.devices: Dict[str, MilesightDevice] = {}
        self._unsubscribers: list[Callable[[], None]] = []

    async def async_close(self) -> None:
        """Cancel MQTT listeners."""
        while self._unsubscribers:
            unsub = self._unsubscribers.pop()
            unsub()

    def get_device(self, dev_eui: str) -> Optional[MilesightDevice]:
        return self.devices.get(dev_eui)

    def register_mqtt(self, unsub: Callable[[], None]) -> None:
        self._unsubscribers.append(unsub)

    async def async_handle_join(self, msg: mqtt.ReceiveMessage) -> None:
        """Handle join messages."""
        payload = msg.payload
        data: Dict[str, object] = {}
        dev_eui: Optional[str] = None
        model: Optional[str] = None
        try:
            data = json.loads(payload)
            dev_eui = str(
                data.get("dev_eui")
                or data.get("devEui")
                or data.get("devEUI")
                or data.get("deveui")
            )
            model = str(data.get("model") or "").lower() or None
        except json.JSONDecodeError:
            dev_eui = payload.strip()

        topic_dev_eui, topic_model = self._parse_topic(msg.topic)
        if topic_dev_eui and not dev_eui:
            dev_eui = topic_dev_eui
        if topic_model:
            model = topic_model

        if not dev_eui:
            _LOGGER.warning("Join payload missing dev_eui: %s", payload)
            return

        if not model:
            model = "wt101"  # default to earliest supported

        name = data.get(ATTR_NAME) if isinstance(data, dict) else None
        await self._async_add_or_update_device(
            dev_eui, name=name, model=model, attributes=data
        )

    async def async_handle_uplink(self, msg: mqtt.ReceiveMessage) -> None:
        """Handle uplink messages."""
        parsed = self._parse_uplink(msg.payload, msg.topic)
        if not parsed:
            _LOGGER.warning("Ignoring unparsable uplink: %s", msg.payload)
            return

        dev_eui = parsed["dev_eui"]
        raw = parsed.get("bytes")
        model = parsed.get("model")

        if parsed.get("telemetry") is not None:
            decoded = parsed["telemetry"]
        else:
            try:
                decoded = decode_payload(model, raw)
            except DecodeError as err:
                _LOGGER.warning("Failed to decode uplink for %s (%s): %s", dev_eui, model, err)
                return

        await self._async_add_or_update_device(
            dev_eui,
            model=model,
            attributes=parsed.get("meta", {}),
            telemetry=decoded,
        )

    async def _async_add_or_update_device(
        self,
        dev_eui: str,
        name: Optional[str] = None,
        model: Optional[str] = None,
        attributes: Optional[Dict[str, object]] = None,
        telemetry: Optional[Dict[str, object]] = None,
    ) -> None:
        """Create a new device entry or update an existing one."""
        dev_eui = dev_eui.lower()
        model_key = (model or "wt101").lower()
        dev = self.devices.get(dev_eui)
        if not dev:
            dev = MilesightDevice(dev_eui=dev_eui, name=name, model=model_key)
            self.devices[dev_eui] = dev
            async_dispatcher_send(
                self.hass, SIGNAL_NEW_DEVICE.format(entry_id=self.entry_id), dev_eui
            )

        dev.last_seen = datetime.now(timezone.utc)
        if name:
            dev.name = name
        if model:
            dev.model = model_key
        if attributes:
            dev.attributes.update(attributes)
        if telemetry:
            dev.telemetry.update(telemetry)

        await self._async_sync_device_registry(dev)

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
        )

    @callback
    def _parse_uplink(
        self, payload: str, topic: str | None = None
    ) -> Optional[Dict[str, object]]:
        """Extract metadata and bytes from different payload shapes."""
        topic_dev_eui, topic_model = self._parse_topic(topic)

        # Try JSON first
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            data = None

        if isinstance(data, dict):
            dev_eui = str(
                data.get("dev_eui")
                or data.get("devEui")
                or data.get("devEUI")
                or data.get("deveui")
                or data.get("DevEUI_uplink", {}).get("DevEUI")
            )
            if not dev_eui:
                dev_eui = topic_dev_eui
            if not dev_eui:
                return None

            model = str(data.get("model") or "").lower() or topic_model
            raw_bytes = self._extract_bytes(data)
            if raw_bytes is None:
                meta = {
                    key: data[key]
                    for key in ("f_port", "fcnt", "rssi", "snr", "timestamp")
                    if key in data
                }
                telemetry = {
                    k: v
                    for k, v in data.items()
                    if k not in ("dev_eui", "devEui", "devEUI", "deveui", "DevEUI_uplink", "model")
                }
                return {
                    "dev_eui": dev_eui,
                    "bytes": None,
                    "meta": meta,
                    "model": model,
                    "telemetry": telemetry,
                }

            meta = {
                key: data[key]
                for key in ("f_port", "fcnt", "rssi", "snr", "timestamp")
                if key in data
            }
            return {
                "dev_eui": dev_eui,
                "bytes": raw_bytes,
                "meta": meta,
                "model": model,
            }

        # If not JSON assume raw hex/base64 string
        payload_str = (payload or "").strip()
        if not payload_str:
            return None

        try:
            raw_bytes = bytes.fromhex(payload_str.replace(" ", ""))
        except ValueError:
            try:
                raw_bytes = base64.b64decode(payload_str, validate=True)
            except Exception:
                return None

        if not topic_dev_eui:
            return None
        return {
            "dev_eui": topic_dev_eui,
            "bytes": raw_bytes,
            "meta": {},
            "model": topic_model,
        }

    def _parse_topic(self, topic: str | None) -> tuple[Optional[str], Optional[str]]:
        """Extract dev_eui and model from topic milesight/{model}/{dev_eui}/<type>."""
        if not topic:
            return None, None
        parts = topic.split("/")
        if len(parts) < 4 or parts[0] != "milesight":
            return None, None
        model = parts[1].lower() if parts[1] else None
        dev_eui_raw = parts[2]
        dev_eui = (
            dev_eui_raw.replace(":", "").replace("-", "").lower()
            if dev_eui_raw
            else None
        )
        return dev_eui, model

    def _extract_bytes(self, data: Dict[str, object]) -> Optional[bytes]:
        """Extract raw payload bytes from multiple common keys."""
        if "data" in data and isinstance(data["data"], str):
            try:
                return base64.b64decode(data["data"], validate=True)
            except Exception:
                pass

        for key in ("payload_hex", "payload", "frm_payload"):
            if isinstance(data.get(key), str):
                try:
                    return bytes.fromhex(data[key])
                except ValueError:
                    continue

        if isinstance(data.get("payload_raw"), (list, tuple)):
            return bytes(data["payload_raw"])

        if isinstance(data.get("bytes"), (list, tuple)):
            return bytes(data["bytes"])

        return None

    def serialize_devices(self) -> list[dict]:
        """Return a list of devices for the frontend view."""
        devices = []
        for dev in self.devices.values():
            devices.append(
                {
                    "dev_eui": dev.dev_eui,
                    "name": dev.name or dev.dev_eui,
                    "model": dev.model,
                    "last_seen": dev.last_seen.isoformat(),
                    "telemetry": dev.telemetry,
                    "attributes": dev.attributes,
                }
            )
        return devices
