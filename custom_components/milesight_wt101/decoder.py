"""Decoder for Milesight WT101 uplink payloads."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List

_LOGGER = logging.getLogger(__name__)

try:
    import js2py

    _JS_DECODER_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    js2py = None
    _JS_DECODER_AVAILABLE = False

JS_DECODER_PATH = Path(__file__).parent / "js" / "wt101-decoder.js"
_JS_CONTEXT = None


class DecodeError(Exception):
    """Raised when payload cannot be decoded."""


# Mappings mirror the official JS decoder but only expose telemetry we surface in HA.
_TAMPER_STATUS = {0: "installed", 1: "uninstalled"}
_WINDOW_DETECTION = {0: "normal", 1: "open"}
_MOTOR_CALIBRATION = {
    0: "success",
    1: "fail: out of range",
    2: "fail: uninstalled",
    3: "calibration cleared",
    4: "temperature control disabled",
}
_FREEZE_PROTECTION = {0: "normal", 1: "triggered"}


def _read_uint8(value: int) -> int:
    return value & 0xFF


def _read_int8(value: int) -> int:
    ref = _read_uint8(value)
    return ref - 0x100 if ref > 0x7F else ref


def _read_uint16_le(data: List[int]) -> int:
    value = (data[1] << 8) + data[0]
    return value & 0xFFFF


def _read_int16_le(data: List[int]) -> int:
    ref = _read_uint16_le(data)
    return ref - 0x10000 if ref > 0x7FFF else ref


def _get_value(mapper: Dict[int, str], key: int) -> str:
    return mapper.get(key, "unknown")


def decode_wt101(payload: bytes) -> Dict[str, object]:
    """Decode a raw WT101 payload into a dictionary."""
    if not payload:
        raise DecodeError("empty payload")

    if _JS_DECODER_AVAILABLE and JS_DECODER_PATH.exists():
        try:
            ctx = _get_js_decoder()
            result = ctx.milesightDeviceDecode(list(payload))
            # js2py returns PyJs objects; to_dict flattens nested data.
            if hasattr(result, "to_dict"):
                return result.to_dict()
            return dict(result)
        except Exception as err:  # pragma: no cover - runtime safety
            _LOGGER.warning("JS decoder failed, falling back to Python parser: %s", err)

    # JS decoder works on a list of ints
    bytes_list = list(payload)
    decoded: Dict[str, object] = {}
    idx = 0

    try:
        while idx < len(bytes_list):
            channel_id = bytes_list[idx]
            idx += 1
            if idx >= len(bytes_list):
                break
            channel_type = bytes_list[idx]
            idx += 1

            if channel_id == 0x01 and channel_type == 0x75:
                decoded["battery"] = _read_uint8(bytes_list[idx])
                idx += 1
            elif channel_id == 0x03 and channel_type == 0x67:
                decoded["temperature"] = _read_int16_le(bytes_list[idx : idx + 2]) / 10
                idx += 2
            elif channel_id == 0x04 and channel_type == 0x67:
                decoded["target_temperature"] = _read_int16_le(
                    bytes_list[idx : idx + 2]
                ) / 10
                idx += 2
            elif channel_id == 0x05 and channel_type == 0x92:
                decoded["valve_opening"] = _read_uint8(bytes_list[idx])
                idx += 1
            elif channel_id == 0x06 and channel_type == 0x00:
                decoded["tamper_status"] = _get_value(
                    _TAMPER_STATUS, bytes_list[idx]
                )
                idx += 1
            elif channel_id == 0x07 and channel_type == 0x00:
                decoded["window_detection"] = _get_value(
                    _WINDOW_DETECTION, bytes_list[idx]
                )
                idx += 1
            elif channel_id == 0x08 and channel_type == 0xE5:
                decoded["motor_calibration_result"] = _get_value(
                    _MOTOR_CALIBRATION, bytes_list[idx]
                )
                idx += 1
            elif channel_id == 0x09 and channel_type == 0x90:
                decoded["motor_stroke"] = _read_uint16_le(bytes_list[idx : idx + 2])
                idx += 2
            elif channel_id == 0x0A and channel_type == 0x00:
                decoded["freeze_protection"] = _get_value(
                    _FREEZE_PROTECTION, bytes_list[idx]
                )
                idx += 1
            elif channel_id == 0x0B and channel_type == 0x90:
                decoded["motor_position"] = _read_uint16_le(bytes_list[idx : idx + 2])
                idx += 2
            else:
                # Unknown channel; stop parsing to avoid runaway
                break
    except Exception as exc:
        raise DecodeError(f"failed to decode: {exc}") from exc

    return decoded


def _get_js_decoder():
    """Lazily load the official JS decoder into a js2py context."""
    global _JS_CONTEXT
    if _JS_CONTEXT is None:
        src = JS_DECODER_PATH.read_text(encoding="utf-8")
        ctx = js2py.EvalJs()
        ctx.execute(src)
        _JS_CONTEXT = ctx
    return _JS_CONTEXT
