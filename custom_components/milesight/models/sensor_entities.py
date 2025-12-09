from homeassistant.components.sensor import (
    SensorEntityDescription,
    SensorDeviceClass,
)
from homeassistant.helpers.entity import EntityCategory
from homeassistant.const import PERCENTAGE, UnitOfTemperature

ipso_version = SensorEntityDescription(
    key="ipso_version",
    name="IPSO Version",
    entity_category=EntityCategory.DIAGNOSTIC,
)

hardware_version = SensorEntityDescription(
    key="hardware_version",
    name="Hardware Version",
    entity_category=EntityCategory.DIAGNOSTIC,
)

firmware_version = SensorEntityDescription(
    key="firmware_version",
    name="Firmware Version",
    entity_category=EntityCategory.DIAGNOSTIC,
)

lorawan_class = SensorEntityDescription(
    key="lorawan_class",
    name="LoRaWAN Class",
    entity_category=EntityCategory.DIAGNOSTIC,
)

sn = SensorEntityDescription(
    key="sn",
    name="Serial Number",
    entity_category=EntityCategory.DIAGNOSTIC,
)

tsl_version = SensorEntityDescription(
    key="tsl_version",
    name="TSL Version",
    entity_category=EntityCategory.DIAGNOSTIC,
)

battery = SensorEntityDescription(
    key="battery",
    name="Battery",
    native_unit_of_measurement=PERCENTAGE,
    device_class=SensorDeviceClass.BATTERY,
)

temperature = SensorEntityDescription(
    key="temperature",
    name="Ambient Temperature",
    native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    device_class=SensorDeviceClass.TEMPERATURE,
)

target_temperature = SensorEntityDescription(
    key="target_temperature",
    name="Target Temperature",
    native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    device_class=SensorDeviceClass.TEMPERATURE,
    entity_category=EntityCategory.CONFIG,
)

valve_opening = SensorEntityDescription(
    key="valve_opening",
    name="Valve Opening",
    native_unit_of_measurement=PERCENTAGE,
)

motor_calibration_result = SensorEntityDescription(
    key="motor_calibration_result",
    name="Motor Calibration Result",
)
motor_stroke = SensorEntityDescription(
    key="motor_stroke",
    name="Motor Stroke",
)

motor_position = SensorEntityDescription(
    key="motor_position",
    name="Motor Position",
)

report_interval = SensorEntityDescription(
    key="report_interval",
    name="Report Interval",
    native_unit_of_measurement="min",
    entity_category=EntityCategory.CONFIG,
)
