"""Transaction and format checks for the vendored codec asset updater."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import sync_codecs


COMMIT = "a" * 40


def _metadata(root: Path) -> dict:
    return {
        "source_repository": sync_codecs.SOURCE_REPOSITORY,
        "commit": COMMIT,
        "files": {
            "wt101/wt101.png": {
                "url": f"https://raw.githubusercontent.com/Milesight-IoT/SensorDecoders/{COMMIT}/wt-series/wt101/wt101.png",
                "sha256": "0" * 64,
            }
        },
    }


class SyncCodecTests(unittest.TestCase):
    def test_trusted_url_and_metadata_reject_untrusted_variants(self):
        relative = "wt101/wt101.png"
        self.assertEqual(sync_codecs._trusted_url(relative, "B" * 40).split("/")[5], "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb")
        metadata = _metadata(Path("."))
        for field, value in (
            ("source_repository", "https://evil.example/SensorDecoders"),
            ("commit", "short"),
            ("sha256", "not-a-sha"),
            ("url", "http://raw.githubusercontent.com/Milesight-IoT/SensorDecoders/a/wt-series/wt101/wt101.png"),
            ("url", f"https://raw.githubusercontent.com/other/repo/{COMMIT}/wt-series/{relative}"),
            ("url", f"https://raw.githubusercontent.com/Milesight-IoT/SensorDecoders/{COMMIT}/other/{relative}"),
        ):
            candidate = json.loads(json.dumps(metadata))
            if field == "url":
                candidate["files"][relative][field] = value
            elif field == "sha256":
                candidate["files"][relative][field] = value
            else:
                candidate[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                sync_codecs._validate_metadata(candidate)

    def test_asset_format_sanity(self):
        sync_codecs._validate_asset("x.png", b"\x89PNG\r\n\x1a\nrest")
        sync_codecs._validate_asset("x-codec.json", b'{"object": []}')
        sync_codecs._validate_asset("x-decoder.js", b"function milesightDeviceDecode() {}")
        sync_codecs._validate_asset("x-encoder.js", b"function milesightDeviceEncode() {}")
        for relative, content in (("x.png", b"no"), ("x.json", b"{}"), ("x.js", b"function decode() {}")):
            with self.subTest(relative=relative):
                with self.assertRaises(ValueError):
                    sync_codecs._validate_asset(relative, content)

    def test_transaction_rolls_back_second_asset_write(self):
        with tempfile.TemporaryDirectory() as directory:
            first, second = Path(directory) / "first", Path(directory) / "second"
            first.write_bytes(b"old-first")
            calls = 0
            real_write = sync_codecs._write_atomically

            def fail_second(path, content):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("simulated asset write failure")
                real_write(path, content)

            with patch.object(sync_codecs, "_write_atomically", side_effect=fail_second):
                with self.assertRaises(OSError):
                    sync_codecs._apply_transaction([(first, b"new-first"), (second, b"new-second")])
            self.assertEqual(first.read_bytes(), b"old-first")
            self.assertFalse(second.exists())

    def test_transaction_rolls_back_metadata_write(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            asset, metadata = root / "asset", root / "metadata.json"
            asset.write_bytes(b"old")
            metadata.write_bytes(b"old-metadata")
            real_write = sync_codecs._write_atomically
            calls = 0

            def fail_metadata(path, content):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("metadata failure")
                real_write(path, content)

            with patch.object(sync_codecs, "_write_atomically", side_effect=fail_metadata):
                with self.assertRaises(OSError):
                    sync_codecs._apply_transaction([(asset, b"new"), (metadata, b"new-metadata")])
            self.assertEqual(asset.read_bytes(), b"old")
            self.assertEqual(metadata.read_bytes(), b"old-metadata")

    def test_update_preparation_downloads_and_validates_before_apply(self):
        metadata = _metadata(Path("."))
        content = b"\x89PNG\r\n\x1a\nvalid"
        metadata["files"]["wt101/wt101.png"]["sha256"] = hashlib.sha256(content).hexdigest()
        with patch.object(sync_codecs, "_download", return_value=content):
            replacements = sync_codecs._prepare_update(metadata)
        self.assertEqual(replacements[0][1], content)
        self.assertEqual(replacements[-1][0], sync_codecs.METADATA)


if __name__ == "__main__":
    unittest.main()
