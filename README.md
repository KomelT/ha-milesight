# Milesight for Home Assistant

[![Open your Home Assistant instance and add this repository in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=KomelT&repository=ha-milesight&category=integration)

Custom integration that listens to MQTT join/uplink topics, auto-discovers Milesight devices (model-aware) and exposes telemetry as entities. WT101 is supported out of the box; more models can be added via the `SensorDecoders` submodule (decoders/encoders are loaded from there).

## Features
- Configurable MQTT topics for join/uplink/downlink (via config flow)
- Uplink payload decoding using official Milesight JS decoders (via `js2py`)
- Dynamic device/entity creation based on the model (WT101 included)
- No built-in panel; use HA entities/services directly

## Expected MQTT payloads
- Topic pattern: `milesight/{model}/{dev_eui}/uplink` (defaults to wildcards `milesight/+/+/uplink`, same for join/downlink).
- **Join topic**: JSON containing `dev_eui` (e.g. `{"dev_eui": "A1B2C3D4E5F6A7B8", "name": "Living Room"}`) or the DevEUI as plain text. DevEUI and model are also parsed from the topic path.
- **Uplink topic**: JSON with `dev_eui` plus one of `data` (base64), `payload_hex`/`payload` (hex string), `payload_raw`/`bytes` (array). Plain hex/base64 payloads without JSON are accepted if the DevEUI is in the topic.

## Sending downlinks / setpoints
- Service: `milesight.send_command`
- Data:
  - `dev_eui` (required)
  - `model` (optional, defaults to `wt101`)
  - `payload` (required dict), e.g. `{"target_temperature": 22}` for WT101
- The integration encodes the payload with the model's JS encoder from the `SensorDecoders` submodule and publishes it to the downlink topic (default `milesight/{model}/{dev_eui}/downlink`; respects your configured template, replacing `+` or `{model}`/`{dev_eui}`).

## Development notes
- Integration domain: `milesight`
- Frontend assets: `custom_components/milesight/www/index.html`
- API endpoint backing the panel: `GET /api/milesight/devices`

## Prerequisites (required before installing Milesight)
1. Install the **Mosquitto broker** add-on in Home Assistant.
2. Create an MQTT user (username/password) in Home Assistant.
3. Start the Mosquitto add-on.
4. Configure the built-in **MQTT** integration in Home Assistant with that user.

## Installation (HACS custom repo)
1. Add this repository as a custom integration in HACS (or use the button at the top).
2. Install and restart Home Assistant.
3. Add the integration from **Settings -> Devices & Services -> Add Integration -> Milesight** and set your MQTT topics.
