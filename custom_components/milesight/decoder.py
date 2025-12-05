"""Decoder loader for Milesight devices."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional

_LOGGER = logging.getLogger(__name__)

# Optional JS runtime
try:
    import js2py

    _JS_AVAILABLE = True
except Exception:  # pragma: no cover
    js2py = None
    _JS_AVAILABLE = False

REPO_ROOT = Path(__file__).resolve().parents[2]
SENSOR_DECODERS_ROOT = REPO_ROOT / "SensorDecoders"
_JS_CACHE: Dict[str, object] = {}
_DECODER_PATH_CACHE: Dict[str, Optional[Path]] = {}


class DecodeError(Exception):
    """Raised when payload cannot be decoded."""


def decode_payload(model: str, payload: bytes) -> Dict[str, object]:
    """Decode a payload for a given model."""
    model_key = (model or "").lower()
    if not model_key:
        raise DecodeError("device model is required to decode payload")
    if not payload:
        raise DecodeError("empty payload")

    # Try JS decoder if available
    if _JS_AVAILABLE:
        decoded = _decode_with_js(model_key, payload)
        if decoded is not None:
            return decoded

    raise DecodeError(f"no decoder for model {model_key}")


def _decode_with_js(model: str, payload: bytes) -> Optional[Dict[str, object]]:
    """Execute the JS decoder for the model."""
    js_file = _find_decoder_path(model)
    if not js_file:
        return None

    try:
        ctx = _JS_CACHE.get(str(js_file))
        if ctx is None:
            ctx = js2py.EvalJs()
            ctx.execute(js_file.read_text(encoding="utf-8"))
            _JS_CACHE[str(js_file)] = ctx
        result = ctx.milesightDeviceDecode(list(payload))
        if hasattr(result, "to_dict"):
            return result.to_dict()
        return dict(result)
    except Exception as err:  # pragma: no cover - runtime safety
        _LOGGER.warning("JS decoder failed for %s via %s: %s", model, js_file, err)
        return None


def _find_decoder_path(model: str) -> Optional[Path]:
    """Locate a decoder JS file from the SensorDecoders submodule."""
    if model in _DECODER_PATH_CACHE:
        return _DECODER_PATH_CACHE[model]

    # Look into the SensorDecoders submodule if present
    if SENSOR_DECODERS_ROOT.exists():
        matches = list(SENSOR_DECODERS_ROOT.rglob(f"{model}-decoder.js"))
        if matches:
            _DECODER_PATH_CACHE[model] = matches[0]
            return matches[0]

    _DECODER_PATH_CACHE[model] = None
    return None
