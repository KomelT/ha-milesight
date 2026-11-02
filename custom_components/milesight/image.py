"""Vendored product images for Milesight devices."""

from __future__ import annotations

import logging

from homeassistant.components.image import ImageEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.util import dt as dt_util
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .codec_runtime import CodecError, load_image_asset
from .const import DOMAIN, SIGNAL_NEW_DEVICE
from .manager import MilesightDevice, MilesightManager

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up product image entities and subscribe to newly discovered devices."""
    manager: MilesightManager = hass.data[DOMAIN][entry.entry_id]
    try:
        image = await hass.async_add_executor_job(load_image_asset, "WT101")
    except (CodecError, OSError) as err:
        _LOGGER.warning("Unable to load vendored product image: %s", err)
        return
    image_last_updated = dt_util.utcnow()

    @callback
    def _async_add_device(dev_eui: str) -> None:
        device = manager.get_device(dev_eui)
        if device is None or device.model.upper() != "WT101":
            return
        async_add_entities([MilesightProductImage(hass, device, image, image_last_updated)])

    for dev_eui in list(manager.devices):
        _async_add_device(dev_eui)

    entry.async_on_unload(
        async_dispatcher_connect(
            hass, SIGNAL_NEW_DEVICE.format(entry_id=entry.entry_id), _async_add_device
        )
    )


class MilesightProductImage(ImageEntity):
    """A read-only local product image attached to a Milesight device."""

    _attr_content_type = "image/png"
    _attr_should_poll = False
    _attr_has_entity_name = True
    _attr_name = "Product image"

    def __init__(
        self,
        hass: HomeAssistant,
        device: MilesightDevice,
        image: bytes,
        image_last_updated,
    ) -> None:
        super().__init__(hass)
        self._image = image
        self._attr_image_last_updated = image_last_updated
        self._dev_eui = device.dev_eui.lower()
        self._attr_unique_id = f"{self._dev_eui}_product_image"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, self._dev_eui)})

    def image(self) -> bytes:
        """Return the already loaded local image bytes."""
        return self._image
