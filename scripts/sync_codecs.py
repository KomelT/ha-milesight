"""Verify, restore, or intentionally upgrade pinned local codec assets."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
METADATA = ROOT / "custom_components/milesight/codecs/metadata.json"
CODEC_ROOT = ROOT / "custom_components/milesight/codecs"
SOURCE_REPOSITORY = "https://github.com/Milesight-IoT/SensorDecoders"
RAW_HOST = "raw.githubusercontent.com"
COMMIT_RE = re.compile(r"^[0-9a-fA-F]{40}$")


def _safe_destination(relative: str) -> Path:
    root = CODEC_ROOT.resolve()
    destination = (root / relative).resolve()
    if destination != root and root not in destination.parents:
        raise ValueError(f"asset path escapes codec root: {relative}")
    return destination


def _validate_metadata(metadata: dict) -> None:
    if metadata.get("source_repository") != SOURCE_REPOSITORY:
        raise ValueError("metadata source_repository is not trusted")
    commit = metadata.get("commit")
    if not isinstance(commit, str) or not COMMIT_RE.fullmatch(commit):
        raise ValueError("metadata commit must be a 40-character hexadecimal SHA")
    if not isinstance(metadata.get("files"), dict):
        raise ValueError("metadata files must be an object")
    commit = commit.lower()
    for relative, record in metadata["files"].items():
        if not isinstance(relative, str) or not relative or relative.startswith(("/", "\\")):
            raise ValueError(f"invalid metadata asset path: {relative}")
        _safe_destination(relative)
        if not isinstance(record, dict):
            raise ValueError(f"invalid metadata record: {relative}")
        digest = record.get("sha256")
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", digest):
            raise ValueError(f"invalid metadata SHA-256: {relative}")
        expected = f"/Milesight-IoT/SensorDecoders/{commit}/wt-series/{relative}"
        parsed = urlsplit(record.get("url", ""))
        if (parsed.scheme, parsed.netloc, parsed.path, parsed.query, parsed.fragment) != (
            "https", RAW_HOST, expected, "", ""
        ):
            raise ValueError(f"untrusted metadata URL: {relative}")


def _validate_asset(relative: str, content: bytes) -> None:
    """Perform format/sanity validation before applying downloaded content."""
    lower = relative.lower()
    if lower.endswith(".png"):
        if not content.startswith(b"\x89PNG\r\n\x1a\n"):
            raise ValueError(f"invalid PNG asset: {relative}")
    elif lower.endswith(".json"):
        try:
            parsed = json.loads(content.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as err:
            raise ValueError(f"invalid JSON asset: {relative}") from err
        if not isinstance(parsed, dict) or not isinstance(parsed.get("object"), list):
            raise ValueError(f"invalid codec JSON structure: {relative}")
    elif lower.endswith(".js"):
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError as err:
            raise ValueError(f"invalid UTF-8 JavaScript asset: {relative}") from err
        required = "function milesightDeviceDecode" if "decoder" in lower else "function milesightDeviceEncode"
        if not text.strip() or required not in text:
            raise ValueError(f"invalid JavaScript format: {relative}")


def _download(url: str) -> bytes:
    with urlopen(url, timeout=30) as response:  # noqa: S310
        return response.read()


def _write_atomically(destination: Path, content: bytes) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=destination.parent, prefix=f".{destination.name}.")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
        os.replace(temporary, destination)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _apply_transaction(replacements: list[tuple[Path, bytes]]) -> None:
    """Apply replacements with best-effort rollback if an apply operation fails."""
    originals = {path: path.read_bytes() if path.exists() else None for path, _ in replacements}
    applied: list[Path] = []
    try:
        for path, content in replacements:
            applied.append(path)
            _write_atomically(path, content)
    except BaseException as error:
        rollback_errors: list[str] = []
        for path in reversed(applied):
            try:
                original = originals[path]
                if original is None:
                    if path.exists():
                        path.unlink()
                else:
                    _write_atomically(path, original)
            except BaseException as rollback_error:
                rollback_errors.append(f"{path}: {rollback_error!r}")
        if rollback_errors:
            raise RuntimeError(
                f"transaction apply failed ({error!r}); rollback also failed: {'; '.join(rollback_errors)}"
            ) from error
        raise


def _trusted_url(relative: str, commit: str) -> str:
    if not COMMIT_RE.fullmatch(commit):
        raise ValueError("commit must be a 40-character hexadecimal SHA")
    _safe_destination(relative)
    return f"https://{RAW_HOST}/Milesight-IoT/SensorDecoders/{commit.lower()}/wt-series/{relative}"


def _metadata_bytes(metadata: dict) -> bytes:
    return (json.dumps(metadata, indent=2) + "\n").encode("utf-8")


def _prepare_update(metadata: dict) -> list[tuple[Path, bytes]]:
    replacements: list[tuple[Path, bytes]] = []
    for relative, record in metadata["files"].items():
        content = _download(record["url"])
        if hashlib.sha256(content).hexdigest() != record["sha256"]:
            raise RuntimeError(f"downloaded checksum mismatch: {relative}")
        _validate_asset(relative, content)
        replacements.append((_safe_destination(relative), content))
    replacements.append((METADATA, _metadata_bytes(metadata)))
    return replacements


def _upgrade(metadata: dict, commit: str) -> None:
    if not COMMIT_RE.fullmatch(commit):
        raise ValueError("--upgrade-to must be a 40-character hexadecimal commit SHA")
    commit = commit.lower()
    pending: list[tuple[Path, bytes, str]] = []
    for relative in metadata["files"]:
        content = _download(_trusted_url(relative, commit))
        _validate_asset(relative, content)
        pending.append((_safe_destination(relative), content, hashlib.sha256(content).hexdigest()))
    new_metadata = json.loads(json.dumps(metadata))
    new_metadata["commit"] = commit
    for relative, record in new_metadata["files"].items():
        record["url"] = _trusted_url(relative, commit)
        record["sha256"] = next(digest for path, _content, digest in pending if path == _safe_destination(relative))
    replacements = [(path, content) for path, content, _digest in pending]
    replacements.append((METADATA, _metadata_bytes(new_metadata)))
    _apply_transaction(replacements)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--update", action="store_true", help="restore assets from trusted pinned URLs")
    parser.add_argument("--upgrade-to", metavar="COMMIT_SHA", help="upgrade to a reviewed upstream commit")
    args = parser.parse_args()
    if args.update and args.upgrade_to:
        parser.error("--update and --upgrade-to are mutually exclusive")
    metadata = json.loads(METADATA.read_text(encoding="utf-8"))
    _validate_metadata(metadata)
    if args.upgrade_to:
        _upgrade(metadata, args.upgrade_to)
        return 0
    if args.update:
        _apply_transaction(_prepare_update(metadata))
    changed = False
    for relative, record in metadata["files"].items():
        digest = hashlib.sha256(_safe_destination(relative).read_bytes()).hexdigest()
        if digest != record["sha256"]:
            print(f"checksum mismatch: {relative}")
            changed = True
        print(f"ok {relative} {digest}")
    return 1 if changed else 0


if __name__ == "__main__":
    raise SystemExit(main())
