# Rugix Apps Examples

This repository contains industrial Rugix Apps examples that can be built into
Rugix app bundles with `rugix-bundler`.

The examples intentionally focus on edge workloads such as protocol translation,
local buffering, and local process data APIs. They avoid fleet management,
remote access, OTA orchestration, device configuration management, and cloud
telemetry features that would overlap with Nexigon.

## Examples

| Example | Pattern | Main components |
| --- | --- | --- |
| `modbus-mqtt-gateway` | Poll a simulated PLC over Modbus TCP and publish normalized MQTT telemetry. | Python, Eclipse Mosquitto |
| `opcua-mqtt-bridge` | Read machine values from an OPC UA server and bridge them into MQTT. | asyncua, Python, Eclipse Mosquitto |
| `mqtt-edge-historian` | Persist MQTT telemetry locally and expose a small query API. | Python, SQLite, FastAPI, Eclipse Mosquitto |

## Quick Start

Install the current Rugix Bundler release through mise's GitHub backend:

```sh
mise install
```

Build app bundles in `dist/`:

```sh
mise run build
```

`tools/build-bundles.sh` uses Podman on the host to build local helper images
before packaging them with Rugix Bundler.

For a fast structural check without bundling container images:

```sh
tools/build-bundles.sh --no-images
tools/test.sh
```

## VM Testing

The optional VM path uses Rugix Bakery to create a Debian EFI test image with
Rugix Ctrl, Docker, Docker Compose, SSH, and network setup.

The bundled `vm/run-bakery` wrapper pins the latest stable Rugix Bakery release
known at the time of writing, `v0.9.3`. Override it with `RUGIX_VERSION` or
`RUGIX_BAKERY_IMAGE` when testing a newer Bakery image.

```sh
tools/build-test-image.sh
tools/build-bundles.sh
tools/vm-test.sh modbus-mqtt-gateway
```

Each app has its own pytest module under `tests/vm/`. The shared fixture boots
the VM, uploads the selected app bundle, runs `rugix-ctrl apps install`,
activates generation `1`, and waits for `rugix-ctrl apps info` to report the app
as running. The per-app test then checks the workload from inside the app's
Docker Compose service.

Run all VM app tests with:

```sh
tools/vm-test.sh all
```

## Open Source Status

All selected runtime components are open source. See [LICENSES.md](LICENSES.md)
for the component/license matrix. Package versions in helper images are kept in
each service's `requirements.txt`.
