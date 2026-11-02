# TODO

## Completed critical fixes

- [x] Make setup/unload/reload lifecycle explicit and single-config-entry.
- [x] Validate MQTT topics, decoded JSON uplinks, downlinks, device deletion, and freeze protection.
- [x] Keep HTTP views registered once while resolving the active manager per request.
- [x] Add built-in regression coverage for encoder, topic parsing, DevEUI normalization, and booleans.

## Open verification and tests

- [ ] Run integration-level Home Assistant MQTT/config-entry verification.
- [x] Add built-in unittest regression coverage for MQTT filtering/payloads, setup/unload lifecycle, HTTP status responses, and registry cleanup using lightweight HA-compatible mocks.
- [ ] Add real Home Assistant fixture smoke coverage for MQTT/config-entry lifecycle and HTTP/registry integration; the current tests do not replace this integration-level verification.

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

## Web UI and photographs

- [ ] Decide between a custom panel/card UI and `entity_picture`; the standard HA device page has no generic product-photo field.
- [ ] Vendor images locally with attribution; do not hotlink them.

## Release readiness

- [ ] Review documentation and migration behavior.
- [ ] Complete the open verification checklist and release smoke test.
