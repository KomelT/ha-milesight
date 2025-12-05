# Milesight WT101 for Home Assistant (MQTT)

Custom integration that listens to MQTT join/uplink topics, auto-discovers WT101 thermostats and exposes telemetry as entities. A lightweight frontend panel lists all devices and their last values.

## Features
- Configurable MQTT topics for join/uplink/downlink (via config flow)
- Uplink payload decoding using the official Milesight schema
- Dynamic device/ entity creation (battery, ambient/target temperature, valve opening, status flags)
- Built-in panel (`Settings → Devices & Services → Integrations → Milesight WT101 → Open Web UI`) served from the integration
- Uses the official WT101 JavaScript decoder via `js2py` (falls back to a lightweight Python parser if unavailable)

## Expected MQTT payloads
- Topic pattern: `milesight/{model}/{dev_eui}/uplink` (defaults to wildcards `milesight/+/+/uplink`, same for join/downlink).
- **Join topic**: JSON containing `dev_eui` (e.g. `{"dev_eui": "A1B2C3D4E5F6A7B8", "name": "Living Room"}`) or the DevEUI as plain text. DevEUI and model are also parsed from the topic path.
- **Uplink topic**: JSON with `dev_eui` plus one of `data` (base64), `payload_hex`/`payload` (hex string), `payload_raw`/`bytes` (array). Plain hex/base64 payloads without JSON are accepted if the DevEUI is in the topic.

## Development notes
- Integration domain: `milesight_wt101`
- Frontend assets: `custom_components/milesight_wt101/www/index.html`
- API endpoint backing the panel: `GET /api/milesight_wt101/devices`

## Installation (HACS custom repo)
1. Add this repository as a custom integration in HACS.
2. Install and restart Home Assistant.
3. Add the integration from **Settings → Devices & Services → Add Integration → Milesight WT101** and set your MQTT topics.
