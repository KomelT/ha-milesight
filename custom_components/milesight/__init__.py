"""Milesight integration."""

from __future__ import annotations

import logging
import json

from homeassistant.components import mqtt
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
import voluptuous as vol
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_DOWNLINK_TOPIC,
    CONF_JOIN_TOPIC,
    CONF_UPLINK_TOPIC,
    DEFAULT_DOWNLINK_TOPIC,
    DOMAIN,
    PLATFORMS,
)
from .encoder import encode_payload, EncodeError
from .http_view import MilesightDevicesView, MilesightDeviceActionView
from .manager import MilesightManager

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up via YAML (not supported)."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the integration from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    manager = MilesightManager(hass, entry.entry_id)
    hass.data[DOMAIN][entry.entry_id] = manager

    hass.http.register_view(MilesightDevicesView(manager))
    hass.http.register_view(MilesightDeviceActionView(manager))

    # Register MQTT listeners
    join_topic = entry.data[CONF_JOIN_TOPIC]
    uplink_topic = entry.data[CONF_UPLINK_TOPIC]
    downlink_topic = entry.data.get(CONF_DOWNLINK_TOPIC) or DEFAULT_DOWNLINK_TOPIC

    manager.register_mqtt(
        await mqtt.async_subscribe(hass, join_topic, manager.async_handle_join_uplink)
    )
    manager.register_mqtt(
        await mqtt.async_subscribe(hass, uplink_topic, manager.async_handle_join_uplink)
    )
    if downlink_topic:
        manager.register_mqtt(
            await mqtt.async_subscribe(
                hass, downlink_topic, manager.async_handle_join_uplink
            )
        )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _register_services(hass, entry, downlink_topic, manager)
    return True


def _register_services(
    hass: HomeAssistant,
    entry: ConfigEntry,
    topic_template: str,
    manager: MilesightManager,
) -> None:
    """Register services for sending downlinks."""

    async def _handle_send_command(call):
        dev_eui: str = call.data["dev_eui"]
        model: str = call.data.get("model") or "wt101"
        payload: dict = call.data.get("payload") or {}
        topic = _build_downlink_topic(topic_template, model, dev_eui)
        try:
            encoded = encode_payload(model, payload)
        except EncodeError as err:
            raise vol.Invalid(f"Encode failed: {err}") from err
        # If encoder returns a normalized downlink dict, publish as JSON; else hex.
        if isinstance(encoded, dict):
            message = json.dumps(encoded)
        elif isinstance(encoded, (bytes, bytearray, list, tuple)):
            message = bytes(encoded).hex()
        else:
            raise vol.Invalid(f"Unsupported encoded payload type: {type(encoded)}")
        await mqtt.async_publish(hass, topic, message)

    hass.services.async_register(
        DOMAIN,
        "send_command",
        _handle_send_command,
        schema=vol.Schema(
            {
                vol.Required("dev_eui"): str,
                vol.Optional("model", default="wt101"): str,
                vol.Required("payload"): dict,
            }
        ),
    )

    async def _handle_delete_device(call):
        dev_eui: str = call.data["dev_eui"]
        await manager.async_delete_device(dev_eui)

    hass.services.async_register(
        DOMAIN,
        "delete_device",
        _handle_delete_device,
        schema=vol.Schema({vol.Required("dev_eui"): str}),
    )


def _build_downlink_topic(template: str, model: str, dev_eui: str) -> str:
    """Build a downlink topic from a template and identifiers."""
    if not template:
        return f"milesight/{model}/{dev_eui}/downlink"
    if "{model}" in template or "{dev_eui}" in template:
        return template.format(model=model, dev_eui=dev_eui)
    if "+" in template:
        parts = template.split("+", 2)
        filled = []
        replacements = [model, dev_eui]
        repl_idx = 0
        for part in parts:
            filled.append(part)
            if repl_idx < len(replacements):
                filled.append(replacements[repl_idx])
                repl_idx += 1
        return "".join(filled)
    return template
