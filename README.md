# Milesight for Home Assistant

[![Open your Home Assistant instance and add this repository in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=KomelT&repository=ha-milesight&category=integration)

Custom integration that listens to MQTT join/uplink topics, auto-discovers Milesight devices (model-aware) and exposes telemetry as entities.

## Features
- Configurable MQTT topics for join/uplink/downlink (via config flow)
- Uplink payload decoding using official Milesight JS decoders (via `js2py`)
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
