"""Sensor descriptions for WT101."""

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntityDescription,
)
from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntityDescription
from homeassistant.const import PERCENTAGE, UnitOfTemperature

"""definitions of WT101 sensor and binary sensor descriptions from SensorDecoders/wt-series/wt101/wt101-codec.json"""

WT101_SENSORS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="ipso_version",
        name="IPSO Version",
    ),
    SensorEntityDescription(
        key="hardware_version",
        name="Hardware Version",
    ),
    SensorEntityDescription(
        key="firmware_version",
        name="Firmware Version",
    ),
    SensorEntityDescription(
        key="lorawan_class",
        name="LoRaWAN Class",
    ),
    SensorEntityDescription(
        key="sn",
        name="Serial Number",
    ),
    SensorEntityDescription(
        key="tsl_version",
        name="TSL Version",
    ),
    SensorEntityDescription(
        key="battery",
        name="Battery",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
    ),
    SensorEntityDescription(
        key="temperature",
        name="Ambient Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
    ),
    SensorEntityDescription(
        key="target_temperature",
        name="Target Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
    ),
    SensorEntityDescription(
        key="valve_opening",
        name="Valve Opening",
        native_unit_of_measurement=PERCENTAGE,
    ),
    SensorEntityDescription(
        key="motor_calibration_result",
        name="Motor Calibration Result",
    ),
    SensorEntityDescription(
        key="motor_stroke",
        name="Motor Stroke",
    ),
    SensorEntityDescription(
        key="motor_position",
        name="Motor Position",
    ),
    # time_zone
    SensorEntityDescription(
        key="report_interval",
        name="Report Interval",
        native_unit_of_measurement="min",
    ),
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
        device_class=BinarySensorDeviceClass.POWER
    ),
    # sync_time
    BinarySensorEntityDescription(
        key="time_sync_enable",
        name="Sync Time Enabled",
        device_class=BinarySensorDeviceClass.POWER
    ),
    BinarySensorEntityDescription(
        key="report_status",
        name="Report Status",
        device_class=BinarySensorDeviceClass.POWER
    ),
    BinarySensorEntityDescription(
        key="child_lock_config.enable",
        name="Child Lock",
        device_class=BinarySensorDeviceClass.POWER
    ),
)
