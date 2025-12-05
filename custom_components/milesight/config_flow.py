"""Config flow for Milesight MQTT integration."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_DOWNLINK_TOPIC,
    CONF_JOIN_TOPIC,
    CONF_UPLINK_TOPIC,
    DEFAULT_DOWNLINK_TOPIC,
    DEFAULT_JOIN_TOPIC,
    DEFAULT_UPLINK_TOPIC,
    DOMAIN,
)


def _schema(user_input: dict | None = None) -> vol.Schema:
    defaults = user_input or {}
    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=defaults.get(CONF_NAME, "Milesight MQTT")): str,
            vol.Required(CONF_JOIN_TOPIC, default=defaults.get(CONF_JOIN_TOPIC, DEFAULT_JOIN_TOPIC)): str,
            vol.Required(CONF_UPLINK_TOPIC, default=defaults.get(CONF_UPLINK_TOPIC, DEFAULT_UPLINK_TOPIC)): str,
            vol.Optional(CONF_DOWNLINK_TOPIC, default=defaults.get(CONF_DOWNLINK_TOPIC, DEFAULT_DOWNLINK_TOPIC)): str,
        }
    )


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for the integration."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

        return self.async_show_form(step_id="user", data_schema=_schema(), errors={})


async def async_get_options_flow(entry: config_entries.ConfigEntry) -> config_entries.OptionsFlow:
    return OptionsFlowHandler(entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options for the integration."""

    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        self.config_entry = entry

    async def async_step_init(self, user_input=None) -> FlowResult:
        if user_input is not None:
            data = {**self.config_entry.data, **user_input}
            self.hass.config_entries.async_update_entry(self.config_entry, data=data)
            return self.async_create_entry(title="", data={})

        return self.async_show_form(
            step_id="init",
            data_schema=_schema({**self.config_entry.data, **self.config_entry.options}),
        )
