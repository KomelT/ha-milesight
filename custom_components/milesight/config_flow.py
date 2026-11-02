"""Config flow for Milesight integration."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME
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


def _validate_topic_filter(value: str) -> str:
    """Validate a topic filter with model and DevEUI wildcards."""
    parts = value.split("/")
    if "#" in value or any("+" in part and part != "+" for part in parts):
        raise vol.Invalid("topic wildcards must be standalone '+' segments")
    if parts.count("+") != 2:
        raise vol.Invalid("topic must contain exactly two '+' wildcards and no '#'")
    if any(not part for part in parts):
        raise vol.Invalid("topic must not contain empty segments")
    return value


def _validate_downlink_template(value: str) -> str:
    parts = value.split("/")
    if "#" in value or any(not part for part in parts):
        raise vol.Invalid("downlink topic must not contain '#' or empty segments")
    if any("+" in part and part != "+" for part in parts):
        raise vol.Invalid("topic wildcards must be standalone '+' segments")
    if "{" in value and "}" in value:
        if not {"{model}", "{dev_eui}"} <= set(value.replace("/", " ").split()):
            raise vol.Invalid("downlink topic must contain model and DevEUI placeholders")
        return value
    if parts.count("+") != 2:
        raise vol.Invalid("downlink topic must not contain '#'")
    return value


def _schema(user_input: dict | None = None) -> vol.Schema:
    defaults = user_input or {}
    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=defaults.get(CONF_NAME, "Milesight")): str,
            vol.Required(
                CONF_JOIN_TOPIC,
                default=defaults.get(CONF_JOIN_TOPIC, DEFAULT_JOIN_TOPIC),
            ): vol.All(str, _validate_topic_filter),
            vol.Required(
                CONF_UPLINK_TOPIC,
                default=defaults.get(CONF_UPLINK_TOPIC, DEFAULT_UPLINK_TOPIC),
            ): vol.All(str, _validate_topic_filter),
            vol.Optional(
                CONF_DOWNLINK_TOPIC,
                default=defaults.get(CONF_DOWNLINK_TOPIC, DEFAULT_DOWNLINK_TOPIC),
            ): vol.All(str, _validate_downlink_template),
        }
    )


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for the integration."""

    VERSION = 1

    @staticmethod
    def async_get_options_flow(entry: config_entries.ConfigEntry):
        return OptionsFlowHandler(entry)

    async def async_step_user(self, user_input=None) -> FlowResult:
        if user_input is not None:
            if self._async_current_entries():
                return self.async_abort(reason="single_instance_allowed")
            return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

        return self.async_show_form(step_id="user", data_schema=_schema(), errors={})

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
            data_schema=_schema(
                {**self.config_entry.data, **self.config_entry.options}
            ),
        )
