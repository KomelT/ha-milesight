"""Sensor descriptions for WT101."""

from homeassistant.components.sensor import (
    SensorEntityDescription,
)
from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntityDescription,
)
from predefined_sensor_entity_description import (
    ipso_version,
    hardware_version,
    firmware_version,
    lorawan_class,
    sn,
    tsl_version,
    battery,
    temperature,
    target_temperature,
    valve_opening,
    motor_calibration_result,
    motor_stroke,
    motor_position,
    report_interval,
)

"""definitions of WT101 sensor and binary sensor descriptions from SensorDecoders/wt-series/wt101/wt101-codec.json"""

WT101_SENSORS: tuple[SensorEntityDescription, ...] = (
    ipso_version,
    hardware_version,
    firmware_version,
    lorawan_class,
    sn,
    tsl_version,
    battery,
    temperature,
    target_temperature,
    valve_opening,
    motor_calibration_result,
    motor_stroke,
    motor_position,
    report_interval,
)

WT101_BINARIES: tuple[BinarySensorEntityDescription, ...] = (
    BinarySensorEntityDescription(
        key="device_status",
        name="Device Status",
        device_class=BinarySensorDeviceClass.POWER,
    ),
    BinarySensorEntityDescription(
        key="tamper_status",
        name="Tamper Status",
        device_class=BinarySensorDeviceClass.TAMPER,
    ),
    BinarySensorEntityDescription(
        key="window_detection",
        name="Window",
        device_class=BinarySensorDeviceClass.WINDOW,
    ),
    BinarySensorEntityDescription(
        key="freeze_protection",
        name="Freeze Protection",
        device_class=BinarySensorDeviceClass.POWER,
    ),
    BinarySensorEntityDescription(
        key="reboot",
        name="Reboot Scheduled",
        device_class=BinarySensorDeviceClass.POWER,
    ),
    # sync_time
    BinarySensorEntityDescription(
        key="time_sync_enable",
        name="Sync Time Enabled",
        device_class=BinarySensorDeviceClass.POWER,
    ),
    BinarySensorEntityDescription(
        key="report_status",
        name="Report Status",
        device_class=BinarySensorDeviceClass.POWER,
    ),
)
