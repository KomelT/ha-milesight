<img src="https://github.com/home-assistant/brands/blob/master/custom_integrations/milesight/logo.png" alt="Milesight Integration for Home Assistant" width="300">

# Milesight Integration for Home Assistant

[![Open your Home Assistant instance and add this repository in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=KomelT&repository=ha-milesight&category=integration)

Custom integration that listens to MQTT join/uplink topics, auto-discovers Milesight devices (model-aware) and exposes telemetry as entities.

## Features
- Configurable MQTT topics for join/uplink/downlink (via config flow)
- Uplink payloads are accepted as already-decoded JSON objects or WT101 raw gateway data
- Dynamic device/entity creation based on the model (WT101 included)
- No built-in panel; use HA entities/services directly

## Prerequisites (required before installing Milesight)
1. Install the **Mosquitto broker** add-on in Home Assistant.
2. Create an MQTT user (username/password) in Home Assistant.
3. Start the Mosquitto add-on.
4. Configure the built-in **MQTT** integration in Home Assistant with that user.

## Installation (HACS custom repo)
1. Add this repository as a custom integration in HACS (or use the button at the top).
2. Install and restart Home Assistant.
3. Add the integration from **Settings -> Devices & Services -> Add Integration -> Milesight** and set your MQTT topics.

## Milesight GW setup (send data to Home Assistant)
After installing the integration, configure MQTT on your Milesight gateway:

1. Open Milesight GW web UI.
2. Go to MQTT settings (or Application -> MQTT).
3. Set broker connection to your Home Assistant MQTT broker:
   - Host/IP: your HA or Mosquitto host
   - Port: `1883` (or your TLS port)
   - Username/password: MQTT user created in Home Assistant
4. Enable publish for uplink/join events.
5. Set topics to match the Home Assistant integration defaults:
   - Join topic: `milesight/{model}/{dev_eui}/join`
   - Uplink topic: `milesight/{model}/{dev_eui}/uplink`
   - Downlink topic: `milesight/{model}/{dev_eui}/downlink`
6. Save/apply and restart MQTT service on the gateway (if required).
7. Trigger one device uplink and verify entities appear in Home Assistant.

The integration includes pinned, official Milesight WT101 GPL-3.0 decoder and
encoder code locally. A gateway may publish decoded JSON or its normal wrapper
with `data` as base64 (hex and byte-list forms are also accepted for WT101).
There is no runtime GitHub access. The vendored PNG is not currently displayed.

To verify pinned assets, run `python scripts/sync_codecs.py`; it is verify-only
by default. `--update` only re-downloads the exact metadata URLs and accepts
the files when their already trusted SHA-256 values match. Changing a commit
or checksum requires a manual, reviewable metadata change.

The downlink service uses the official WT101 encoder and publishes
`{confirmed, fport, data}` JSON.

quickjs-ng provides wheels for Windows, macOS, and Linux on selected x86_64,
i686, and aarch64 architectures; installation is not guaranteed on unsupported
Home Assistant architectures such as 32-bit ARM.

## Disclaimer
This project is an independent, community-driven repository and is not affiliated with, endorsed by, or in any way officially connected with Milesight Technology Co., Ltd. All product names, logos, and brands are property of their respective owners.
