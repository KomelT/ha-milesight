# TODO

## Completed critical fixes

- [x] Make setup/unload/reload lifecycle explicit and single-config-entry.
- [x] Validate MQTT topics, decoded JSON uplinks, downlinks, device deletion, and freeze protection.
- [x] Keep HTTP views registered once while resolving the active manager per request.
- [x] Add built-in regression coverage for encoder, topic parsing, DevEUI normalization, and booleans.

## Open verification and tests

- [x] Define the release verification checklist and automated regression coverage.
- [x] Add built-in unittest regression coverage for MQTT filtering/payloads, setup/unload lifecycle, HTTP status responses, and registry cleanup using lightweight HA-compatible mocks.

## Official Milesight codec/assets plan

- [x] Decide codec licensing and attribution requirements before vendoring.
- [x] Pin an upstream release/commit and record checksums.
- [x] Build a WT101 pilot using upstream assets.
- [x] Decide on a JavaScript runtime adapter; use quickjs-ng with isolation and an executor.
- [x] Add a synchronization script for pinned upstream assets.
- [x] Add tests against upstream sample payloads.
- [ ] Expand to additional models only after the pilot is stable.

The upstream https://github.com/Milesight-IoT/SensorDecoders repository provides
`decoder.js`, `encoder.js`, `codec.json`, and PNG assets per model, and is
licensed GPL-3.0. Prefer vendoring a pinned release/commit without runtime
GitHub access.

## Native product images

- [x] Expose vendored WT101 photography as a native read-only Home Assistant image entity.
- [x] Vendor images locally with attribution; do not hotlink them.

## Release readiness

- [x] Review documentation and migration behavior.
- [x] Add CI checks for the versioned development baseline.
- [x] Run the physical Home Assistant + gateway smoke test (the only release verification requiring the user's environment).
