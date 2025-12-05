"""Sensor descriptions for WT101."""

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntityDescription,
)
from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntityDescription
from homeassistant.const import PERCENTAGE, UnitOfTemperature

WT101_SENSORS: tuple[SensorEntityDescription, ...] = (
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
        key="tamper_status",
        name="Installation Status",
    ),
    SensorEntityDescription(
        key="window_detection",
        name="Open Window Detection",
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
        key="freeze_protection",
        name="Freeze Protection",
    ),
    SensorEntityDescription(
        key="motor_position",
        name="Motor Position",
    ),
)

WT101_BINARIES: tuple[BinarySensorEntityDescription, ...] = (
    BinarySensorEntityDescription(
        key="window_detection",
        name="Open Window",
        device_class=BinarySensorDeviceClass.WINDOW,
    ),
    BinarySensorEntityDescription(
        key="tamper_status",
        name="Uninstalled",
        device_class=BinarySensorDeviceClass.TAMPER,
    ),
    BinarySensorEntityDescription(
        key="freeze_protection",
        name="Freeze Protection",
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    BinarySensorEntityDescription(
        key="motor_calibration_result",
        name="Motor Calibration Issue",
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
)
