# -*- coding: utf-8 -*-
"""
Payload Encoder (Python port)

Port Milesight WT101 encoderja iz JavaScripta v Python.
Ključna funkcija: milesightDeviceEncode(payload: dict) -> list[int]
"""

RAW_VALUE = 0x01  # če želiš uporabljati številčne vrednosti (0/1 ipd.), pusti 0x01


class Buffer:
    def __init__(self, size: int):
        self.buffer = [0] * size
        self.offset = 0

    def _write(self, value: int, byte_length: int, little_endian: bool = True):
        for index in range(byte_length):
            if little_endian:
                shift = index << 3
            else:
                shift = (byte_length - 1 - index) << 3
            self.buffer[self.offset + index] = (value >> shift) & 0xFF

    def writeUInt8(self, value: int):
        self._write(value & 0xFF, 1, True)
        self.offset += 1

    def writeInt8(self, value: int):
        if value < 0:
            value = value + 0x100
        self._write(value & 0xFF, 1, True)
        self.offset += 1

    def writeUInt16LE(self, value: int):
        self._write(value & 0xFFFF, 2, True)
        self.offset += 2

    def writeInt16LE(self, value: int):
        if value < 0:
            value = value + 0x10000
        self._write(value & 0xFFFF, 2, True)
        self.offset += 2

    def writeUInt32LE(self, value: int):
        self._write(value & 0xFFFFFFFF, 4, True)
        self.offset += 4

    def writeInt32LE(self, value: int):
        if value < 0:
            value = value + 0x100000000
        self._write(value & 0xFFFFFFFF, 4, True)
        self.offset += 4

    def toBytes(self):
        return self.buffer


def getValues(map_):
    values = []
    for key, val in map_.items():
        if RAW_VALUE:
            values.append(int(key))
        else:
            values.append(val)
    return values


def getValue(map_, value):
    if RAW_VALUE:
        return value

    for key, val in map_.items():
        if val == value:
            return int(key)

    raise ValueError("not match in " + repr(map_))


def milesightDeviceEncode(payload: dict) -> list[int]:
    encoded = []

    if "reboot" in payload:
        encoded += reboot(payload["reboot"])
    if "report_status" in payload:
        encoded += reportStatus(payload["report_status"])
    if "report_heating_date" in payload:
        encoded += reportHeatingDate(payload["report_heating_date"])
    if "report_heating_schedule" in payload:
        encoded += reportHeatingSchedule(payload["report_heating_schedule"])
    if "sync_time" in payload:
        encoded += syncTime(payload["sync_time"])
    if "report_interval" in payload:
        encoded += setReportInterval(payload["report_interval"])
    if "time_zone" in payload:
        encoded += setTimeZone(payload["time_zone"])
    if "time_sync_enable" in payload:
        encoded += setTimeSyncEnable(payload["time_sync_enable"])
    if "temperature_calibration_settings" in payload:
        encoded += setTemperatureCalibration(
            payload["temperature_calibration_settings"]
        )
    if "temperature_control" in payload and "enable" in payload["temperature_control"]:
        encoded += setTemperatureControl(payload["temperature_control"]["enable"])
    if "temperature_control" in payload and "mode" in payload["temperature_control"]:
        encoded += setTemperatureControlMode(payload["temperature_control"]["mode"])
    if "target_temperature" in payload:
        encoded += setTargetTemperature(
            payload["target_temperature"], payload.get("temperature_tolerance")
        )
    if "target_temperature_range" in payload:
        encoded += setTargetTemperatureRange(payload["target_temperature_range"])
    if "open_window_detection" in payload:
        encoded += setOpenWindowDetection(payload["open_window_detection"])
    if "restore_open_window_detection" in payload:
        encoded += restoreOpenWindowDetection(payload["restore_open_window_detection"])
    if "valve_opening" in payload:
        encoded += setValveOpening(payload["valve_opening"])
    if "valve_calibration" in payload:
        encoded += setValveCalibration(payload["valve_calibration"])
    if "valve_control_algorithm" in payload:
        encoded += setValveControlAlgorithm(payload["valve_control_algorithm"])
    if "freeze_protection_config" in payload:
        encoded += setFreezeProtection(payload["freeze_protection_config"])
    if "child_lock_config" in payload:
        encoded += setChildLockEnable(payload["child_lock_config"]["enable"])
    if "offline_control_mode" in payload:
        encoded += setOfflineControlMode(payload["offline_control_mode"])
    if "outside_temperature" in payload:
        encoded += setOutsideTemperature(payload["outside_temperature"])
    if "outside_temperature_control" in payload:
        encoded += setOutsideTemperatureControl(payload["outside_temperature_control"])
    if "display_ambient_temperature" in payload:
        encoded += setDisplayAmbientTemperature(payload["display_ambient_temperature"])
    if "window_detection_valve_strategy" in payload:
        encoded += setWindowDetectionValveStrategy(
            payload["window_detection_valve_strategy"]
        )
    if "dst_config" in payload:
        encoded += setDaylightSavingTime(payload["dst_config"])
    if "effective_stroke" in payload:
        encoded += setEffectiveStroke(payload["effective_stroke"])
    if "heating_date" in payload:
        encoded += setHeatingDate(payload["heating_date"])
    if "heating_schedule" in payload:
        for item in payload["heating_schedule"]:
            encoded += setHeatingSchedule(item)
    if "change_report_enable" in payload:
        encoded += setChangeReportEnable(payload["change_report_enable"])

    return encoded


# --- posamezne funkcije ---


def reboot(reboot_val: int):
    yes_no_map = {0: "no", 1: "yes"}
    yes_no_values = getValues(yes_no_map)
    if reboot_val not in yes_no_values:
        raise ValueError(f"reboot must be one of {yes_no_values}")

    if getValue(yes_no_map, reboot_val) == 0:
        return []
    return [0xFF, 0x10, 0xFF]


def syncTime(sync_time: int):
    yes_no_map = {0: "no", 1: "yes"}
    yes_no_values = getValues(yes_no_map)
    if sync_time not in yes_no_values:
        raise ValueError(f"sync_time must be one of {yes_no_values}")

    if sync_time == 0:
        return []
    return [0xFF, 0x4A, 0xFF]


def reportStatus(report_status: int):
    yes_no_map = {0: "no", 1: "yes"}
    yes_no_values = getValues(yes_no_map)
    if report_status not in yes_no_values:
        raise ValueError(f"report_status must be one of {yes_no_values}")

    if getValue(yes_no_map, report_status) == 0:
        return []
    return [0xFF, 0x28, 0x00]


def reportHeatingDate(report_heating_date: int):
    yes_no_map = {0: "no", 1: "yes"}
    yes_no_values = getValues(yes_no_map)
    if report_heating_date not in yes_no_values:
        raise ValueError(f"report_heating_date must be one of {yes_no_values}")

    if getValue(yes_no_map, report_heating_date) == 0:
        return []
    return [0xFF, 0x28, 0x01]


def reportHeatingSchedule(report_heating_schedule: int):
    yes_no_map = {0: "no", 1: "yes"}
    yes_no_values = getValues(yes_no_map)
    if report_heating_schedule not in yes_no_values:
        raise ValueError(f"report_heating_schedule must be one of {yes_no_values}")

    if getValue(yes_no_map, report_heating_schedule) == 0:
        return []
    return [0xFF, 0x28, 0x02]


def setReportInterval(report_interval: int):
    if not isinstance(report_interval, (int, float)):
        raise ValueError("report_interval must be a number")
    if report_interval < 1 or report_interval > 1440:
        raise ValueError("report_interval must be between 1 and 1440")

    buf = Buffer(5)
    buf.writeUInt8(0xFF)
    buf.writeUInt8(0x8E)
    buf.writeUInt8(0x00)
    buf.writeUInt16LE(int(report_interval))
    return buf.toBytes()


def setTimeSyncEnable(time_sync_enable: int):
    enable_map = {0: "disable", 2: "enable"}
    enable_values = getValues(enable_map)
    if time_sync_enable not in enable_values:
        raise ValueError(f"time_sync_enable must be one of {enable_values}")

    buf = Buffer(3)
    buf.writeUInt8(0xFF)
    buf.writeUInt8(0x3B)
    buf.writeUInt8(getValue(enable_map, time_sync_enable))
    return buf.toBytes()


def setTemperatureCalibration(temperature_calibration_settings: dict):
    enable = temperature_calibration_settings.get("enable")
    calibration_value = temperature_calibration_settings.get("calibration_value")

    enable_map = {0: "disable", 1: "enable"}
    enable_values = getValues(enable_map)
    if enable not in enable_values:
        raise ValueError(
            f"temperature_calibration_settings.enable must be one of {enable_values}"
        )
    if enable and not isinstance(calibration_value, (int, float)):
        raise ValueError(
            "temperature_calibration_settings.calibration_value must be a number"
        )

    buf = Buffer(5)
    buf.writeUInt8(0xFF)
    buf.writeUInt8(0xAB)
    buf.writeUInt8(getValue(enable_map, enable))
    buf.writeInt16LE(
        int(calibration_value * 10 if calibration_value is not None else 0)
    )
    return buf.toBytes()


def setTemperatureControl(enable: int):
    enable_map = {0: "disable", 1: "enable"}
    enable_values = getValues(enable_map)
    if enable not in enable_values:
        raise ValueError(f"temperature_control.enable must be one of {enable_values}")

    buf = Buffer(3)
    buf.writeUInt8(0xFF)
    buf.writeUInt8(0xB3)
    buf.writeUInt8(getValue(enable_map, enable))
    return buf.toBytes()


def setTemperatureControlMode(mode: int):
    temperature_control_mode_map = {0: "auto", 1: "manual"}
    values = getValues(temperature_control_mode_map)
    if mode not in values:
        raise ValueError(f"temperature_control.mode must be one of {values}")

    buf = Buffer(3)
    buf.writeUInt8(0xFF)
    buf.writeUInt8(0xAE)
    buf.writeUInt8(getValue(temperature_control_mode_map, mode))
    return buf.toBytes()


def setTargetTemperature(target_temperature, temperature_tolerance):
    if not isinstance(target_temperature, (int, float)):
        raise ValueError("target_temperature must be a number")
    if not isinstance(temperature_tolerance, (int, float)):
        raise ValueError("temperature_tolerance must be a number")

    # Bytes: FF B1 <temp> <tolerance_lo> <tolerance_hi>
    buf = Buffer(5)
    buf.writeUInt8(0xFF)
    buf.writeUInt8(0xB1)
    buf.writeInt8(int(target_temperature))
    buf.writeUInt16LE(int(temperature_tolerance * 10))
    return buf.toBytes()


def setTargetTemperatureRange(target_temperature_range: dict):
    min_val = target_temperature_range.get("min")
    max_val = target_temperature_range.get("max")

    if not isinstance(min_val, (int, float)):
        raise ValueError("target_temperature_range.min must be a number")
    if min_val < 5 or min_val > 15:
        raise ValueError("target_temperature_range.min must be between 5 and 15")
    if not isinstance(max_val, (int, float)):
        raise ValueError("target_temperature_range.max must be a number")
    if max_val < 16 or max_val > 35:
        raise ValueError("target_temperature_range.max must be between 16 and 35")

    buf = Buffer(4)
    buf.writeUInt8(0xF9)
    buf.writeUInt8(0x35)
    buf.writeUInt8(int(min_val))
    buf.writeUInt8(int(max_val))
    return buf.toBytes()


def setOpenWindowDetection(open_window_detection: dict):
    enable = open_window_detection.get("enable")
    temperature_threshold = open_window_detection.get("temperature_threshold")
    time_val = open_window_detection.get("time")

    enable_map = {0: "disable", 1: "enable"}
    enable_values = getValues(enable_map)
    if enable not in enable_values:
        raise ValueError(f"open_window_detection.enable must be one of {enable_values}")
    if enable and not isinstance(temperature_threshold, (int, float)):
        raise ValueError("open_window_detection.temperature_threshold must be a number")
    if enable and not isinstance(time_val, (int, float)):
        raise ValueError("open_window_detection.time must be a number")

    buf = Buffer(6)
    buf.writeUInt8(0xFF)
    buf.writeUInt8(0xAF)
    buf.writeUInt8(getValue(enable_map, enable))
    buf.writeInt8(
        int(temperature_threshold * 10 if temperature_threshold is not None else 0)
    )
    buf.writeUInt16LE(int(time_val if time_val is not None else 0))
    return buf.toBytes()


def restoreOpenWindowDetection(restore_open_window_detection: int):
    yes_no_map = {0: "no", 1: "yes"}
    yes_no_values = getValues(yes_no_map)
    if restore_open_window_detection not in yes_no_values:
        raise ValueError(
            f"restore_open_window_detection must be one of {yes_no_values}"
        )

    if getValue(yes_no_map, restore_open_window_detection) == 0:
        return []
    return [0xFF, 0x57, 0xFF]


def setValveOpening(valve_opening: int):
    if not isinstance(valve_opening, (int, float)):
        raise ValueError("valve_opening must be a number")
    if valve_opening < 0 or valve_opening > 100:
        raise ValueError("valve_opening must be between 0 and 100")

    buf = Buffer(3)
    buf.writeUInt8(0xFF)
    buf.writeUInt8(0xB4)
    buf.writeUInt8(int(valve_opening))
    return buf.toBytes()


def setValveCalibration(valve_calibration: int):
    yes_no_map = {0: "no", 1: "yes"}
    yes_no_values = getValues(yes_no_map)
    if valve_calibration not in yes_no_values:
        raise ValueError(f"valve_calibration must be one of {yes_no_values}")

    if getValue(yes_no_map, valve_calibration) == 0:
        return []
    return [0xFF, 0xAD, 0xFF]


def setValveControlAlgorithm(valve_control_algorithm: int):
    valve_control_algorithm_map = {0: "rate", 1: "pid"}
    values = getValues(valve_control_algorithm_map)
    if valve_control_algorithm not in values:
        raise ValueError(f"valve_control_algorithm must be one of {values}")

    buf = Buffer(3)
    buf.writeUInt8(0xFF)
    buf.writeUInt8(0xAC)
    buf.writeUInt8(getValue(valve_control_algorithm_map, valve_control_algorithm))
    return buf.toBytes()


def setFreezeProtection(freeze_protection_config: dict):
    enable = freeze_protection_config.get("enable")
    temperature = freeze_protection_config.get("temperature")

    enable_map = {0: "disable", 1: "enable"}
    enable_values = getValues(enable_map)
    if enable not in enable_values:
        raise ValueError(
            f"freeze_protection_config.enable must be one of {enable_values}"
        )
    if enable and not isinstance(temperature, (int, float)):
        raise ValueError("freeze_protection_config.temperature must be a number")

    buf = Buffer(5)
    buf.writeUInt8(0xFF)
    buf.writeUInt8(0xB0)
    buf.writeUInt8(getValue(enable_map, enable))
    buf.writeInt16LE(int(temperature * 10 if temperature is not None else 0))
    return buf.toBytes()


def setChildLockEnable(enable: int):
    enable_map = {0: "disable", 1: "enable"}
    enable_values = getValues(enable_map)
    if enable not in enable_values:
        raise ValueError(f"child_lock_config.enable must be one of {enable_values}")

    buf = Buffer(3)
    buf.writeUInt8(0xFF)
    buf.writeUInt8(0x25)
    buf.writeUInt8(getValue(enable_map, enable))
    return buf.toBytes()


def setOfflineControlMode(offline_control_mode: int):
    offline_control_mode_map = {
        0: "keep",
        1: "embedded temperature control",
        2: "off",
    }
    values = getValues(offline_control_mode_map)
    if offline_control_mode not in values:
        raise ValueError(f"offline_control_mode must be one of {values}")

    buf = Buffer(3)
    buf.writeUInt8(0xFF)
    buf.writeUInt8(0xF8)
    buf.writeUInt8(getValue(offline_control_mode_map, offline_control_mode))
    return buf.toBytes()


def setOutsideTemperature(outside_temperature: int):
    if not isinstance(outside_temperature, (int, float)):
        raise ValueError("outside_temperature must be a number")

    buf = Buffer(4)
    buf.writeUInt8(0x03)
    buf.writeInt16LE(int(outside_temperature * 10))
    buf.writeUInt8(0xFF)
    return buf.toBytes()


def setOutsideTemperatureControl(outside_temperature_control: dict):
    enable = outside_temperature_control.get("enable")
    timeout = outside_temperature_control.get("timeout")

    enable_map = {0: "disable", 1: "enable"}
    enable_values = getValues(enable_map)
    if enable not in enable_values:
        raise ValueError(
            f"outside_temperature_control.enable must be one of {enable_values}"
        )
    if enable and not isinstance(timeout, (int, float)):
        raise ValueError("outside_temperature_control.timeout must be a number")
    if enable and (timeout < 3 or timeout > 60):
        raise ValueError("outside_temperature_control.timeout must be between 3 and 60")

    buf = Buffer(4)
    buf.writeUInt8(0xFF)
    buf.writeUInt8(0xC4)
    buf.writeUInt8(getValue(enable_map, enable))
    buf.writeUInt8(int(timeout if timeout is not None else 0))
    return buf.toBytes()


def setDisplayAmbientTemperature(display_ambient_temperature: int):
    enable_map = {0: "disable", 1: "enable"}
    enable_values = getValues(enable_map)
    if display_ambient_temperature not in enable_values:
        raise ValueError(f"display_ambient_temperature must be one of {enable_values}")

    buf = Buffer(3)
    buf.writeUInt8(0xF9)
    buf.writeUInt8(0x36)
    buf.writeUInt8(getValue(enable_map, display_ambient_temperature))
    return buf.toBytes()


def setWindowDetectionValveStrategy(window_detection_valve_strategy: int):
    window_detection_valve_strategy_map = {0: "keep", 1: "close"}
    values = getValues(window_detection_valve_strategy_map)
    if window_detection_valve_strategy not in values:
        raise ValueError(f"window_detection_valve_strategy must be one of {values}")

    buf = Buffer(3)
    buf.writeUInt8(0xF9)
    buf.writeUInt8(0x37)
    buf.writeUInt8(
        getValue(window_detection_valve_strategy_map, window_detection_valve_strategy)
    )
    return buf.toBytes()


def setDaylightSavingTime(dst_config: dict):
    enable = dst_config.get("enable")
    offset = dst_config.get("offset")
    start_month = dst_config.get("start_month")
    start_week_num = dst_config.get("start_week_num")
    start_week_day = dst_config.get("start_week_day")
    start_time = dst_config.get("start_time")
    end_month = dst_config.get("end_month")
    end_week_num = dst_config.get("end_week_num")
    end_week_day = dst_config.get("end_week_day")
    end_time = dst_config.get("end_time")

    enable_map = {0: "disable", 1: "enable"}
    enable_values = getValues(enable_map)
    if enable not in enable_values:
        raise ValueError(f"dst_config.enable must be one of {enable_values}")

    month_values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    if enable and start_month not in month_values:
        raise ValueError(f"dst_config.start_month must be one of {month_values}")
    if enable and end_month not in month_values:
        raise ValueError(f"dst_config.end_month must be one of {month_values}")

    week_values = [1, 2, 3, 4, 5, 6, 7]
    if enable and start_week_day not in week_values:
        raise ValueError(f"dst_config.start_week_day must be one of {week_values}")

    buf = Buffer(12)
    buf.writeUInt8(0xFF)
    buf.writeUInt8(0xBA)
    buf.writeUInt8(getValue(enable_map, enable))
    buf.writeInt8(int(offset))
    buf.writeUInt8(int(start_month))
    buf.writeUInt8((int(start_week_num) << 4) | int(start_week_day))
    buf.writeUInt16LE(int(start_time))
    buf.writeUInt8(int(end_month))
    buf.writeUInt8((int(end_week_num) << 4) | int(end_week_day))
    buf.writeUInt16LE(int(end_time))
    return buf.toBytes()


def setTimeZone(time_zone: int):
    timezone_map = {
        -720: "UTC-12",
        -660: "UTC-11",
        -600: "UTC-10",
        -570: "UTC-9:30",
        -540: "UTC-9",
        -480: "UTC-8",
        -420: "UTC-7",
        -360: "UTC-6",
        -300: "UTC-5",
        -240: "UTC-4",
        -210: "UTC-3:30",
        -180: "UTC-3",
        -120: "UTC-2",
        -60: "UTC-1",
        0: "UTC",
        60: "UTC+1",
        120: "UTC+2",
        180: "UTC+3",
        210: "UTC+3:30",
        240: "UTC+4",
        270: "UTC+4:30",
        300: "UTC+5",
        330: "UTC+5:30",
        345: "UTC+5:45",
        360: "UTC+6",
        390: "UTC+6:30",
        420: "UTC+7",
        480: "UTC+8",
        540: "UTC+9",
        570: "UTC+9:30",
        600: "UTC+10",
        630: "UTC+10:30",
        660: "UTC+11",
        720: "UTC+12",
        765: "UTC+12:45",
        780: "UTC+13",
        840: "UTC+14",
    }

    timezone_values = getValues(timezone_map)
    if time_zone not in timezone_values:
        raise ValueError(f"time_zone must be one of {timezone_values}")

    buf = Buffer(4)
    buf.writeUInt8(0xFF)
    buf.writeUInt8(0xBD)
    buf.writeInt16LE(getValue(timezone_map, time_zone))
    return buf.toBytes()


def setEffectiveStroke(effective_stroke: dict):
    enable = effective_stroke.get("enable")
    rate = effective_stroke.get("rate")

    enable_map = {0: "disable", 1: "enable"}
    enable_values = getValues(enable_map)
    if enable not in enable_values:
        raise ValueError(f"effective_stroke.enable must be one of {enable_values}")
    if enable and (rate < 0 or rate > 100):
        raise ValueError("effective_stroke.rate must be between 0 and 100")

    buf = Buffer(4)
    buf.writeUInt8(0xF9)
    buf.writeUInt8(0x38)
    buf.writeUInt8(getValue(enable_map, enable))
    buf.writeUInt8(int(rate if rate is not None else 0))
    return buf.toBytes()


def setHeatingDate(heating_date: dict):
    enable = heating_date.get("enable")
    start_month = heating_date.get("start_month")
    start_day = heating_date.get("start_day")
    end_month = heating_date.get("end_month")
    end_day = heating_date.get("end_day")
    report_interval = heating_date.get("report_interval")

    enable_map = {0: "disable", 1: "enable"}
    enable_values = getValues(enable_map)
    if enable not in enable_values:
        raise ValueError(f"heating_date.enable must be one of {enable_values}")

    month_values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    if enable and start_month not in month_values:
        raise ValueError(f"heating_date.start_month must be one of {month_values}")
    if enable and end_month not in month_values:
        raise ValueError(f"heating_date.end_month must be one of {month_values}")

    buf = Buffer(9)
    buf.writeUInt8(0xF9)
    buf.writeUInt8(0x33)
    buf.writeUInt8(getValue(enable_map, enable))
    buf.writeUInt16LE(int(report_interval))
    buf.writeUInt8(int(start_month))
    buf.writeUInt8(int(start_day))
    buf.writeUInt8(int(end_month))
    buf.writeUInt8(int(end_day))
    return buf.toBytes()


def setHeatingSchedule(heating_schedule: dict):
    index = heating_schedule.get("index")
    enable = heating_schedule.get("enable")
    temperature_control_mode = heating_schedule.get("temperature_control_mode")
    value = heating_schedule.get("value")
    report_interval = heating_schedule.get("report_interval")
    execute_time = heating_schedule.get("execute_time")
    week_recycle = heating_schedule.get("week_recycle", {})

    if index < 1 or index > 16:
        raise ValueError("heating_schedule._item.index must be between 1 and 16")

    enable_map = {0: "disable", 1: "enable"}
    enable_values = getValues(enable_map)
    if enable not in enable_values:
        raise ValueError(
            f"heating_schedule._item.enable must be one of {enable_values}"
        )

    temperature_control_mode_map = {0: "auto", 1: "manual"}
    tcm_values = getValues(temperature_control_mode_map)
    if temperature_control_mode not in tcm_values:
        raise ValueError(
            f"heating_schedule._item.temperature_control_mode must be one of {tcm_values}"
        )

    if enable and (report_interval < 1 or report_interval > 1440):
        raise ValueError(
            "heating_schedule._item.report_interval must be between 1 and 1440"
        )

    week_day_offset = {
        "monday": 1,
        "tuesday": 2,
        "wednesday": 3,
        "thursday": 4,
        "friday": 5,
        "saturday": 6,
        "sunday": 7,
    }

    days = 0x00
    for day, offset in week_day_offset.items():
        if day in week_recycle:
            val = week_recycle[day]
            if val not in enable_values:
                raise ValueError(
                    f"heating_schedule._item.week_recycle.{day} must be one of {enable_values}"
                )
            days |= getValue(enable_map, val) << offset

    buf = Buffer(11)
    buf.writeUInt8(0xF9)
    buf.writeUInt8(0x34)
    buf.writeUInt8(index - 1)
    buf.writeUInt8(getValue(enable_map, enable))
    buf.writeUInt8(getValue(temperature_control_mode_map, temperature_control_mode))
    buf.writeUInt8(int(value))
    buf.writeUInt16LE(int(report_interval))
    buf.writeUInt16LE(int(execute_time))
    buf.writeUInt8(days)
    return buf.toBytes()


def setChangeReportEnable(change_report_enable: int):
    enable_map = {0: "disable", 1: "enable"}
    enable_values = getValues(enable_map)
    if change_report_enable not in enable_values:
        raise ValueError(f"change_report_enable must be one of {enable_values}")

    buf = Buffer(3)
    buf.writeUInt8(0xF9)
    buf.writeUInt8(0x3A)
    buf.writeUInt8(getValue(enable_map, change_report_enable))
    return buf.toBytes()
