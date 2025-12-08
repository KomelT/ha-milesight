"""Pure-Python encoder loader for Milesight devices (no JS runtime)."""

from __future__ import annotations

import base64
import importlib.util
import logging
from pathlib import Path
from typing import Dict, Optional, Any

_LOGGER = logging.getLogger(__name__)

ENCODER_ROOT = Path(__file__).parent / "decoders"
_ENCODER_CACHE: Dict[Path, Any] = {}


class EncodeError(Exception):
    """Raised when payload cannot be encoded."""


def encode_payload(model: str, payload: Dict[str, object]) -> bytes:
    """Encode a downlink payload for a given model using a Python encoder file."""
    model_key = (model or "").strip().lower()
    if not model_key:
        raise EncodeError("device model is required to encode payload")
    if not payload:
        raise EncodeError("empty payload")

    encoder_path = _find_encoder_path(model_key)
    if not encoder_path:
        raise EncodeError(f"encoder for model {model_key} not found")

    encoder_mod = _load_encoder(encoder_path)

    try:
        if hasattr(encoder_mod, "encode"):
            result = encoder_mod.encode(payload)
        elif hasattr(encoder_mod, "milesightDeviceEncode"):
            result = encoder_mod.milesightDeviceEncode(payload)
        else:
            raise EncodeError(f"encoder function not found in {encoder_path.name}")
    except EncodeError:
        raise
    except Exception as err:  # pragma: no cover - runtime safety
        raise EncodeError(f"failed to encode payload: {err}") from err

    return _normalize_downlink(result, encoder_path, payload)


def _find_encoder_path(model: str) -> Optional[Path]:
    """Locate a Python encoder file in decoders/{model}/{model}-encoder.py (or -encode.py)."""
    candidates = [
        ENCODER_ROOT / model / f"{model}-encoder.py",
        ENCODER_ROOT / model / f"{model}-encode.py",
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


def _load_encoder(path: Path):
    """Load (and cache) a Python module from the encoder path."""
    mod = _ENCODER_CACHE.get(path)
    if mod:
        return mod
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise EncodeError(f"cannot load encoder from {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[assignment]
    _ENCODER_CACHE[path] = mod
    return mod


def _as_bytes(result: object, path: Path) -> bytes:
    """Coerce encoder output into bytes."""
    if result is None:
        raise EncodeError(f"encoder {path.name} returned nothing")
    if isinstance(result, bytes):
        return result
    if isinstance(result, bytearray):
        return bytes(result)
    if isinstance(result, (list, tuple)):
        try:
            return bytes(result)
        except Exception as err:  # pragma: no cover - defensive
            raise EncodeError(f"encoder {path.name} returned non-byte list: {err}") from err
    raise EncodeError(f"encoder {path.name} returned unsupported type {type(result)}")


def _normalize_downlink(result: Any, path: Path, payload: Dict[str, object]) -> Dict[str, object]:
    """Normalize encoder output to {confirmed, fport, data(base64)}."""
    confirmed = bool(payload.get("confirmed", True))
    fport = int(payload.get("fport", 85))

    if isinstance(result, dict):
        # Allow encoder to override fport/confirmed and raw data
        confirmed = bool(result.get("confirmed", confirmed))
        fport = int(result.get("fport", fport))
        data_obj = result.get("data") or result.get("bytes")
        if data_obj is None:
            raise EncodeError(f"encoder {path.name} returned dict without data/bytes")
        data_bytes = _to_bytes(data_obj, path)
    else:
        data_bytes = _to_bytes(result, path)

    return {
        "confirmed": confirmed,
        "fport": fport,
        "data": base64.b64encode(data_bytes).decode("ascii"),
    }


def _to_bytes(data: Any, path: Path) -> bytes:
    """Coerce encoder output data to bytes."""
    if isinstance(data, bytes):
        return data
    if isinstance(data, bytearray):
        return bytes(data)
    if isinstance(data, (list, tuple)):
        try:
            return bytes(data)
        except Exception as err:  # pragma: no cover - defensive
            raise EncodeError(f"encoder {path.name} returned non-byte list: {err}") from err
    if isinstance(data, str):
        # Assume hex or base64 string
        try:
            return bytes.fromhex(data)
        except Exception:
            try:
                return base64.b64decode(data)
            except Exception:
                raise EncodeError(f"encoder {path.name} returned string data not hex/base64")
    raise EncodeError(f"encoder {path.name} returned unsupported data type {type(data)}")
