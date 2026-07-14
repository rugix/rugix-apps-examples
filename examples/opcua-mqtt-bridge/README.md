# OPC UA to MQTT Bridge

This Rugix App models an industrial gateway that reads values from an OPC UA
machine endpoint and publishes normalized telemetry to a local MQTT broker.

The app contains:

- `opcua-server`: an OPC UA machine simulator with changing process values.
- `bridge`: an OPC UA client that publishes selected nodes to MQTT and writes
  the latest sample to the app data directory.
- `broker`: Eclipse Mosquitto.

This is an application workload example. It does not provide remote access,
fleet management, OTA, device identity, or cloud telemetry.

## Bundle

```sh
../../tools/build-bundles.sh --example opcua-mqtt-bridge
```
