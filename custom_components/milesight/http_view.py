"""HTTP API for Milesight devices."""

from __future__ import annotations

from typing import Any

from homeassistant.components.http import HomeAssistantView
from homeassistant.core import callback

from .manager import MilesightManager


class MilesightDevicesView(HomeAssistantView):
    """Expose devices and last telemetry for the frontend."""

    name = "api:milesight:devices"
    url = "/api/milesight/devices"
    requires_auth = True

    def __init__(self, manager: MilesightManager) -> None:
        self._manager = manager

    @callback
    async def get(self, request) -> Any:  # type: ignore[override]
        return self.json(
            {
                "devices": self._manager.serialize_devices(),
                "pending": self._manager.serialize_pending(),
            }
        )


class MilesightDeviceActionView(HomeAssistantView):
    """Handle approve/ignore actions for pending devices."""

    name = "api:milesight:device_action"
    url = "/api/milesight/device_action"
    requires_auth = True

    def __init__(self, manager: MilesightManager) -> None:
        self._manager = manager

    async def post(self, request) -> Any:  # type: ignore[override]
        data = await request.json()
        dev_eui = data.get("dev_eui")
        action = data.get("action")
        model = data.get("model")
        name = data.get("name")

        if action == "approve":
            await self._manager.async_approve_device(dev_eui, name=name, model=model)
            return self.json({"status": "approved"})
        if action == "ignore":
            await self._manager.async_ignore_device(dev_eui)
            return self.json({"status": "ignored"})
        if action == "delete":
            await self._manager.async_delete_device(dev_eui)
            return self.json({"status": "deleted"})

        return self.json({"error": "invalid action"}, status_code=400)
