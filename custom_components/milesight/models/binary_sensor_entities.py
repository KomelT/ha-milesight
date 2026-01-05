from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntityDescription,
)

device_status = BinarySensorEntityDescription(
    key="device_status",
    name="Device Status",
    device_class=BinarySensorDeviceClass.POWER,
)

tamper_status = BinarySensorEntityDescription(
    key="tamper_status",
    name="Tamper Status",
    device_class=BinarySensorDeviceClass.TAMPER,
)

window_detection = BinarySensorEntityDescription(
    key="window_detection",
    name="Window",
    device_class=BinarySensorDeviceClass.WINDOW,
)

time_sync_enable = BinarySensorEntityDescription(
    key="time_sync_enable",
    name="Sync Time Enabled",
    device_class=BinarySensorDeviceClass.POWER,
)

report_status = BinarySensorEntityDescription(
    key="report_status",
    name="Report Status",
    device_class=BinarySensorDeviceClass.POWER,
)
