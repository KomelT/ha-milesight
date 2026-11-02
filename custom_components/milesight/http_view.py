"""HTTP API for Milesight devices."""

from __future__ import annotations

from homeassistant.components.http import HomeAssistantView, KEY_HASS
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .manager import MilesightManager


def _manager(hass: HomeAssistant) -> MilesightManager | None:
    return next(
        (value for value in hass.data.get(DOMAIN, {}).values()
         if isinstance(value, MilesightManager)),
        None,
    )


class MilesightDevicesView(HomeAssistantView):
    name = "api:milesight:devices"
    url = "/api/milesight/devices"
    requires_auth = True

    async def get(self, request):
        manager = _manager(request.app[KEY_HASS])
        if manager is None:
            return self.json({"error": "Milesight is not active"}, status_code=503)
        return self.json({"devices": manager.serialize_devices()})


class MilesightDeviceActionView(HomeAssistantView):
    name = "api:milesight:device_action"
    url = "/api/milesight/device_action"
    requires_auth = True

    async def post(self, request):
        manager = _manager(request.app[KEY_HASS])
        if manager is None:
            return self.json({"error": "Milesight is not active"}, status_code=503)
        try:
            data = await request.json()
        except (ValueError, TypeError):
            return self.json({"error": "request body must be JSON"}, status_code=400)
        if not isinstance(data, dict):
            return self.json({"error": "request body must be an object"}, status_code=400)
        dev_eui = data.get("dev_eui")
        if not isinstance(dev_eui, str) or not dev_eui.strip():
            return self.json({"error": "dev_eui is required"}, status_code=400)
        if data.get("action") != "delete":
            return self.json({"error": "invalid action"}, status_code=400)
        if not await manager.async_delete_device(dev_eui):
            return self.json({"error": "device not found"}, status_code=404)
        return self.json({"status": "deleted"})
