# Rugix Apps Examples

This repository contains Rugix Apps examples that can be built into Rugix app
bundles with `rugix-bundler`. They range from a small web-server starter app to
industrial edge workloads.

[Rugix](https://rugix.org) is an open-source toolkit for building and
maintaining robust Linux-powered products. Rugix Apps is part of its on-device
application lifecycle support; fleet management, remote access, and rollout
orchestration remain the responsibility of a separate fleet management
solution.

The industrial examples focus on device-local workloads such as protocol
translation, buffering, and process data APIs.

## Examples

| Example | Pattern | Main components |
| --- | --- | --- |
| `python-web-server` | Serve a static local page from a minimal Python container. | Python |
| `modbus-mqtt-gateway` | Poll a simulated PLC over Modbus TCP and publish normalized MQTT telemetry. | Python, Eclipse Mosquitto |
| `opcua-mqtt-bridge` | Read machine values from an OPC UA server and bridge them into MQTT. | asyncua, Python, Eclipse Mosquitto |
| `mqtt-edge-historian` | Persist MQTT telemetry locally and expose a small query API. | Python, SQLite, FastAPI, Eclipse Mosquitto |

## Quick Start

Install Nix with flakes enabled and mise. The native environments support
x86-64 and AArch64 Linux. Install the pinned Rugix Bundler, Nexigon CLI,
Python, and uv through mise:

```sh
mise install
```

Build app bundles in `dist/`:

```sh
mise run build
```

`mise run build` uses Docker on the host to build local helper images
before packaging them with Rugix Bundler.

For a fast structural check without bundling container images:

```sh
mise run build-no-images
mise run test
```

## Prebuilt App Bundles

CI builds every example for `linux/amd64` and `linux/arm64`. Pull requests and
builds of `main` expose the bundles as workflow artifacts. A tagged commit also
creates a GitHub release containing the bundles.

Release filenames identify both the example and target architecture. They use
the architecture names that Rugix Ctrl reports as `host.arch`, such as `x86_64`
and `aarch64`, so tools can pick the bundle that matches a device. For example,
the Python web-server assets are:

```text
python-web-server-x86_64.rugixb
python-web-server-x86_64.rugixb-hash
python-web-server-aarch64.rugixb
python-web-server-aarch64.rugixb-hash
```

The hash files contain the Rugix bundle header hashes produced by
`rugix-bundler hash`. Maintainers can create a release by pushing a tag:

```sh
git tag v0.1.0
git push origin v0.1.0
```

CI also publishes every release to the `default` repository on
`staging.nexigon.dev`, for demos and testing. Each example is a package
of the same name, which must exist. The release becomes a version tagged with
the release tag and `latest`, with the bundles' hashes as asset metadata. See
`scripts/publish-nexigon.sh` for details.

## VM Testing

The optional VM path uses Rugix Bakery to create a Debian EFI test image with
Rugix Ctrl, Docker, Docker Compose, SSH, and network setup.

The bundled `vm/run-bakery` wrapper pins the latest stable Rugix Bakery release
known at the time of writing, `v0.9.3`. Override it with `RUGIX_VERSION` or
`RUGIX_BAKERY_IMAGE` when testing a newer Bakery image.

```sh
mise run test-image
mise run build
mise run vm-test modbus-mqtt-gateway
```

Each app has its own pytest module under `tests/vm/`. The shared fixture boots
the VM, uploads the selected app bundle, runs `rugix-ctrl apps install`,
activates generation `1`, and waits for `rugix-ctrl apps info` to report the app
as running. The per-app test then checks the workload from inside the app's
Docker Compose service.

Run all VM app tests with:

```sh
mise run vm-test all
```

## Open Source Status

All selected runtime components are open source. See [LICENSES.md](LICENSES.md)
for the component/license matrix. Package versions in helper images are kept in
each service's `requirements.txt`.

## Support

This repository is covered by
[Tier 3: Example Integration](https://rugix.org/support-commitment/#tier-example-integration)
of the Rugix Support Commitment.

Mise tasks select Nix for Skopeo, SSH tools, QEMU, and OVMF when needed.
Docker Engine and its CLI must be available for the helper-image builds.
Builds default to `linux/amd64`. For native ARM64 builds, run
`RUGIX_PLATFORM=linux/arm64 mise run build`. The VM test image is x86-64;
on ARM64 hosts, QEMU runs it with software emulation.
Python dependencies are locked in `uv.lock`; VM tests install the pinned
Rugix Testkit dependency without requiring an adjacent checkout. The
`scripts/` directory implements build, collection, and publication steps.
