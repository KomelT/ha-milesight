"""Milesight WT101 MQTT integration."""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components import frontend, mqtt
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_DOWNLINK_TOPIC,
    CONF_JOIN_TOPIC,
    CONF_UPLINK_TOPIC,
    DOMAIN,
    PLATFORMS,
)
from .http_view import MilesightDevicesView
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

    await _async_setup_http(hass, manager)

    # Register MQTT listeners
    join_topic = entry.data[CONF_JOIN_TOPIC]
    uplink_topic = entry.data[CONF_UPLINK_TOPIC]
    downlink_topic = entry.data.get(CONF_DOWNLINK_TOPIC)

    manager.register_mqtt(
        await mqtt.async_subscribe(hass, join_topic, manager.async_handle_join)
    )
    manager.register_mqtt(
        await mqtt.async_subscribe(hass, uplink_topic, manager.async_handle_uplink)
    )
    if downlink_topic:
        manager.register_mqtt(
            await mqtt.async_subscribe(hass, downlink_topic, manager.async_handle_uplink)
        )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _async_setup_http(hass: HomeAssistant, manager: MilesightManager) -> None:
    """Expose frontend assets and API endpoint."""
    www_path = Path(__file__).parent / "www"
    hass.http.register_static_path("/milesight-wt101-frontend", str(www_path), cache_headers=False)
    hass.http.register_view(MilesightDevicesView(manager))
    frontend.async_register_built_in_panel(
        hass,
        component_name="iframe",
        sidebar_title="Milesight WT101",
        sidebar_icon="mdi:radiator",
        frontend_url_path="milesight_wt101",
        config={"url": "/milesight-wt101-frontend/index.html"},
        require_admin=False,
    )


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    manager: MilesightManager = hass.data[DOMAIN].pop(entry.entry_id)
    await manager.async_close()
    await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    frontend.async_remove_panel(hass, "milesight_wt101")
    return True
