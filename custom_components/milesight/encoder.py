"""Encoder loader for Milesight devices."""

from __future__ import annotations

import logging
from typing import Dict

from .decoder import SENSOR_DECODERS_ROOT

_LOGGER = logging.getLogger(__name__)

try:
    import js2py

    _JS_AVAILABLE = True
except Exception:  # pragma: no cover
    js2py = None
    _JS_AVAILABLE = False

_ENCODER_CACHE: Dict[str, object] = {}


class EncodeError(Exception):
    """Raised when payload cannot be encoded."""


def encode_payload(model: str, payload: Dict[str, object]) -> bytes:
    """Encode an object for a given model using JS encoders."""
    if not model:
        raise EncodeError("device model is required to encode payload")
    if not payload:
        raise EncodeError("empty payload")
    if not _JS_AVAILABLE:
        raise EncodeError("js2py is not available to encode payloads")

    js_file = _find_encoder_path(model)
    if js_file is None:
        raise EncodeError(f"encoder for model {model} not found")

    try:
        ctx = _ENCODER_CACHE.get(str(js_file))
        if ctx is None:
            ctx = js2py.EvalJs()
            ctx.execute(js_file.read_text(encoding="utf-8"))
            _ENCODER_CACHE[str(js_file)] = ctx
        if hasattr(ctx, "milesightDeviceEncode"):
            result = ctx.milesightDeviceEncode(payload)
        elif hasattr(ctx, "Encode"):
            result = ctx.Encode(None, payload)
        else:
            raise EncodeError("encoder function not found in JS file")
        encoded_list = list(result)
        return bytes(encoded_list)
    except EncodeError:
        raise
    except Exception as err:  # pragma: no cover - runtime safety
        raise EncodeError(f"failed to encode payload: {err}") from err


def _find_encoder_path(model: str):
    """Locate the encoder JS in the SensorDecoders submodule."""
    matches = list(SENSOR_DECODERS_ROOT.rglob(f"{model}-encoder.js"))
    return matches[0] if matches else None
