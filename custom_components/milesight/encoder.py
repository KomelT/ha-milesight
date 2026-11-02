"""Downlink adapter for vendored JavaScript codecs."""

from __future__ import annotations

import base64
from .codec_runtime import CodecError, encode


class EncodeError(Exception):
    """Raised when payload cannot be encoded."""


def encode_payload(model: str, payload: dict[str, object]) -> dict[str, object]:
    """Return the Home Assistant downlink envelope."""
    if not (model or "").strip():
        raise EncodeError("device model is required to encode payload")
    if not isinstance(payload, dict) or not payload:
        raise EncodeError("empty payload")
    confirmed = payload.get("confirmed", True)
    fport = payload.get("fport", 85)
    if type(confirmed) is not bool:
        raise EncodeError("confirmed must be a boolean")
    if type(fport) is not int or not 1 <= fport <= 223:
        raise EncodeError("fport must be an integer between 1 and 223")
    command = {key: value for key, value in payload.items() if key not in {"confirmed", "fport"}}
    if not command:
        raise EncodeError("empty command")
    try:
        data = encode(model, command)
    except (CodecError, TypeError, ValueError) as err:
        raise EncodeError(str(err)) from err
    return {
        "confirmed": confirmed,
        "fport": fport,
        "data": base64.b64encode(data).decode("ascii"),
    }
