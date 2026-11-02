"""Sandboxed execution of locally vendored Milesight JavaScript codecs."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import quickjs

CODEC_ROOT = Path(__file__).parent / "codecs"
MODEL_ASSETS = {
    "wt101": ("wt101-decoder.js", "wt101-encoder.js", "wt101.png"),
}


class CodecError(Exception):
    """Base error for codec loading or execution failures."""


class CodecModelError(CodecError):
    """The requested model is not a controlled local asset."""


class CodecExecutionError(CodecError):
    """A codec failed or exceeded its execution limits."""


def _model_dir(model: str) -> tuple[str, Path]:
    model_key = model.strip().lower() if isinstance(model, str) else ""
    if model_key not in MODEL_ASSETS or Path(model_key).name != model_key:
        raise CodecModelError(f"unsupported codec model: {model!r}")
    path = (CODEC_ROOT / model_key).resolve()
    if path.parent != CODEC_ROOT.resolve():
        raise CodecModelError("invalid codec model path")
    return model_key, path


def _asset_path(model: str, asset: str) -> Path:
    model_key, model_dir = _model_dir(model)
    filenames = MODEL_ASSETS[model_key]
    if asset not in {"decoder", "encoder", "image"}:
        raise CodecError(f"unknown codec asset: {asset}")
    filename = filenames[{"decoder": 0, "encoder": 1, "image": 2}[asset]]
    root = CODEC_ROOT.resolve()
    path = (model_dir / filename).resolve()
    if root not in path.parents or model_dir not in path.parents:
        raise CodecModelError(f"invalid codec asset path: {filename}")
    return path


def load_image_asset(model: str) -> bytes:
    """Load a controlled local product image and validate its PNG signature."""
    path = _asset_path(model, "image")
    try:
        content = path.read_bytes()
    except (OSError, UnicodeError) as err:
        raise CodecError(f"cannot read image asset {path.name}") from err
    if not content.startswith(b"\x89PNG\r\n\x1a\n"):
        raise CodecError(f"image asset is not a PNG: {path.name}")
    return content


@lru_cache(maxsize=8)
def _read_source(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def _run(model: str, asset: str, expression: str, *, raw_values: bool = False) -> Any:
    path = _asset_path(model, asset)
    try:
        source = _read_source(str(path))
    except (OSError, UnicodeError) as err:
        raise CodecError(f"cannot read codec asset {path.name}") from err
    try:
        context = quickjs.Context()
        context.set_memory_limit(8 * 1024 * 1024)
        context.set_max_stack_size(512 * 1024)
        context.set_time_limit(1.0)
        context.eval(source)
        if raw_values:
            context.eval("RAW_VALUE = 1")
        result_json = context.eval(f"JSON.stringify({expression})")
        if result_json is None:
            raise CodecExecutionError("codec returned undefined")
        return json.loads(result_json)
    except CodecError:
        raise
    except Exception as err:
        raise CodecExecutionError(f"codec execution failed: {err}") from err


def decode(model: str, payload: bytes) -> dict[str, Any]:
    """Decode bytes with a fresh QuickJS context."""
    if not payload:
        raise CodecExecutionError("empty codec payload")
    result = _run(
        model,
        "decoder",
        f"milesightDeviceDecode({json.dumps(list(payload))})",
    )
    if not isinstance(result, dict) or not result:
        raise CodecExecutionError("codec returned an empty/non-object decode")
    return result


def encode(model: str, payload: dict[str, Any]) -> bytes:
    """Encode a command with a fresh QuickJS context."""
    if not payload:
        raise CodecExecutionError("empty codec payload")
    try:
        expression = f"milesightDeviceEncode({json.dumps(payload, separators=(',', ':'))})"
    except Exception as err:
        raise CodecError("payload is not JSON serializable") from err
    result = _run(model, "encoder", expression, raw_values=True)
    if not isinstance(result, list) or not result:
        raise CodecExecutionError("codec returned an empty/non-array encode")
    try:
        return bytes(result)
    except (TypeError, ValueError) as err:
        raise CodecExecutionError("codec returned invalid bytes") from err
