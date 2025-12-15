"""Sensor descriptions for WT101."""

from homeassistant.components.sensor import (
    SensorEntityDescription,
)
from homeassistant.components.binary_sensor import (
    BinarySensorEntityDescription,
)
from .sensor_entities import (
    ipso_version,
    hardware_version,
    firmware_version,
    lorawan_class,
    sn,
    tsl_version,
    battery,
    temperature,
    valve_opening,
    motor_calibration_result,
    motor_stroke,
    motor_position,
    report_interval,
)
from .binary_sensor_entities import (
    device_status,
    tamper_status,
    window_detection,
    reboot,
    time_sync_enable,
    report_status,
)

WT101_SENSORS: tuple[SensorEntityDescription, ...] = (
    ipso_version,
    hardware_version,
    firmware_version,
    lorawan_class,
    sn,
    tsl_version,
    battery,
    temperature,
    valve_opening,
    motor_calibration_result,
    motor_stroke,
    motor_position,
    report_interval,
)

WT101_BINARIES: tuple[BinarySensorEntityDescription, ...] = (
    device_status,
    tamper_status,
    window_detection,
    reboot,
    time_sync_enable,
    report_status,
)
