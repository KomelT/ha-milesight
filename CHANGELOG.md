# Changelog

## Unreleased

- Nothing yet.

## 0.2.0

- Fixed critical setup, unload, reload, HTTP, and entity lifecycle behavior.
- Added official WT101 codecs, raw gateway decoding, and downlink encoding.
- Added a native Home Assistant product image entity.
- Added regression tests, codec synchronization checks, and licensing notices.
- Added a codec updater with all-download/validation-before-apply behavior and
  rollback attempts for detected apply failures; process termination or power
  loss is outside that guarantee.
