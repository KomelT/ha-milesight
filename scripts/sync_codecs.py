"""Verify or refresh pinned local codec assets.

Usage: ``python scripts/sync_codecs.py`` verifies checksums without network.
Use ``--update`` to download the exact trusted URLs and atomically replace
assets only when their existing trusted checksums still match.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
METADATA = ROOT / "custom_components/milesight/codecs/metadata.json"
CODEC_ROOT = ROOT / "custom_components/milesight/codecs"


def _safe_destination(relative: str) -> Path:
    root = CODEC_ROOT.resolve()
    destination = (root / relative).resolve()
    if destination != root and root not in destination.parents:
        raise ValueError(f"asset path escapes codec root: {relative}")
    return destination


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--update",
        action="store_true",
        help="restore assets from trusted pinned URLs when hashes match",
    )
    args = parser.parse_args()
    metadata = json.loads(METADATA.read_text(encoding="utf-8"))
    changed = False
    for relative, record in metadata["files"].items():
        destination = _safe_destination(relative)
        trusted_hash = record["sha256"]
        if args.update:
            with urlopen(record["url"], timeout=30) as response:  # noqa: S310
                content = response.read()
            digest = hashlib.sha256(content).hexdigest()
            if digest != trusted_hash:
                raise RuntimeError(f"downloaded checksum mismatch: {relative}")
            destination.parent.mkdir(parents=True, exist_ok=True)
            fd, temporary = tempfile.mkstemp(dir=destination.parent, prefix=f".{destination.name}.")
            try:
                with os.fdopen(fd, "wb") as handle:
                    handle.write(content)
                os.replace(temporary, destination)
            finally:
                if os.path.exists(temporary):
                    os.unlink(temporary)
        digest = hashlib.sha256(destination.read_bytes()).hexdigest()
        if digest != record["sha256"]:
            print(f"checksum mismatch: {relative}")
            changed = True
        print(f"ok {relative} {digest}")
    return 1 if changed else 0


if __name__ == "__main__":
    raise SystemExit(main())
