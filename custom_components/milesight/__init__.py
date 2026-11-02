"""Milesight integration."""

from __future__ import annotations

import logging
import json
from functools import partial

from homeassistant.components import mqtt
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import (
    ConfigEntryNotReady,
    HomeAssistantError,
    ServiceValidationError,
)
from homeassistant.helpers import config_validation as cv
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
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up via YAML (not supported)."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the integration from a config entry."""
    manager = MilesightManager(
        hass,
        entry.entry_id,
        entry.data[CONF_UPLINK_TOPIC],
        entry.data[CONF_JOIN_TOPIC],
    )

    # Register MQTT listeners
    join_topic = entry.data[CONF_JOIN_TOPIC]
    uplink_topic = entry.data[CONF_UPLINK_TOPIC]
    downlink_topic = entry.data.get(CONF_DOWNLINK_TOPIC) or DEFAULT_DOWNLINK_TOPIC

    try:
        manager.register_mqtt(
            await mqtt.async_subscribe(
                hass,
                join_topic,
                partial(manager.async_handle_join_uplink, topic_filter=join_topic),
            )
        )
        manager.register_mqtt(
            await mqtt.async_subscribe(
                hass,
                uplink_topic,
                partial(manager.async_handle_join_uplink, topic_filter=uplink_topic),
            )
        )
    except HomeAssistantError as err:
        await manager.async_close()
        raise ConfigEntryNotReady(
            "MQTT is not ready. Configure the MQTT integration and broker credentials first."
        ) from err
    except Exception:
        await manager.async_close()
        raise

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = manager
    if not hass.data[DOMAIN].get("_views_registered"):
        hass.http.register_view(MilesightDevicesView())
        hass.http.register_view(MilesightDeviceActionView())
        hass.data[DOMAIN]["_views_registered"] = True

    try:
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    except Exception:
        await manager.async_close()
        hass.data[DOMAIN].pop(entry.entry_id, None)
        raise
    _register_services(hass, entry, downlink_topic)
    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))
    return True


async def _async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload one config entry and its MQTT subscriptions."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if not unloaded:
        return False
    manager = hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    if manager:
        await manager.async_close()
    if hass.services.has_service(DOMAIN, "send_command"):
        hass.services.async_remove(DOMAIN, "send_command")
    if hass.services.has_service(DOMAIN, "delete_device"):
        hass.services.async_remove(DOMAIN, "delete_device")
    return unloaded


def _register_services(
    hass: HomeAssistant,
    entry: ConfigEntry,
    topic_template: str,
) -> None:
    """Register services for sending downlinks."""

    async def _handle_send_command(call):
        dev_eui: str = call.data["dev_eui"].strip()
        manager = next((value for value in hass.data.get(DOMAIN, {}).values()
                        if isinstance(value, MilesightManager)), None)
        if not isinstance(manager, MilesightManager):
            raise ServiceValidationError("Milesight is not active")
        device = manager.get_device(dev_eui)
        if not device:
            raise ServiceValidationError(f"Device {dev_eui} was not found")
        model: str = call.data.get("model") or device.model
        payload: dict = call.data.get("payload") or {}
        topic = _build_downlink_topic(topic_template, model, dev_eui)
        try:
            encoded = encode_payload(model, payload)
        except EncodeError as err:
            raise ServiceValidationError(f"Encode failed: {err}") from err
        # If encoder returns a normalized downlink dict, publish as JSON; else hex.
        if isinstance(encoded, dict):
            message = json.dumps(encoded)
        elif isinstance(encoded, (bytes, bytearray, list, tuple)):
            message = bytes(encoded).hex()
        else:
            raise ServiceValidationError(f"Unsupported encoded payload type: {type(encoded)}")
        await mqtt.async_publish(hass, topic, message)

    hass.services.async_register(
        DOMAIN,
        "send_command",
        _handle_send_command,
        schema=vol.Schema(
            {
                vol.Required("dev_eui"): str,
                vol.Optional("model"): str,
                vol.Required("payload"): dict,
            }
        ),
    )

    async def _handle_delete_device(call):
        dev_eui: str = call.data["dev_eui"]
        manager = next((value for value in hass.data.get(DOMAIN, {}).values()
                        if isinstance(value, MilesightManager)), None)
        if not isinstance(manager, MilesightManager) or not await manager.async_delete_device(dev_eui):
            raise ServiceValidationError(f"Device {dev_eui} was not found")

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
