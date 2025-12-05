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
        return self.json({"devices": self._manager.serialize_devices()})
