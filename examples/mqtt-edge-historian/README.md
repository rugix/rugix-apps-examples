# MQTT Edge Historian

This Rugix App models a local edge historian: MQTT telemetry is persisted on the
device and exposed through a local HTTP API for diagnostics or upstream polling.

The app contains:

- `broker`: Eclipse Mosquitto.
- `publisher`: a machine telemetry simulator that publishes MQTT samples.
- `historian`: an MQTT subscriber that stores samples in SQLite and serves a
  local query API.

This is an application workload example. It does not provide remote access,
fleet management, OTA, device identity, or cloud telemetry.

## Bundle

```sh
../../tools/build-bundles.sh --example mqtt-edge-historian
```
