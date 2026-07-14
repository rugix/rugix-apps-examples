# Modbus to MQTT Gateway

This Rugix App models a common industrial edge workload: read register values
from a PLC-like Modbus TCP endpoint, normalize the data, and publish telemetry
to a local MQTT broker.

The app contains:

- `simulator`: a small Modbus TCP simulator with changing machine values.
- `gateway`: a Modbus polling service that publishes JSON telemetry to MQTT and
  writes the latest sample to the app data directory.
- `broker`: Eclipse Mosquitto.

This is an application workload example. It does not provide remote access,
fleet management, OTA, device identity, or cloud telemetry.

## Bundle

```sh
../../tools/build-bundles.sh --example modbus-mqtt-gateway
```
