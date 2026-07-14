#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP="${1:-modbus-mqtt-gateway}"
IMAGE="${RUGIX_TEST_IMAGE:-"${ROOT}/vm/build/apps-test-amd64/system.img"}"
BUNDLE_DIR="${RUGIX_BUNDLE_DIR:-"${ROOT}/dist"}"
KEY="${RUGIX_TEST_SSH_KEY:-"${ROOT}/vm/ssh/id_ed25519"}"
TESTKIT="${RUGIX_TESTKIT:-"${ROOT}/../rugix-testkit"}"
TARGET="tests/vm"

case "${APP}" in
    all)
        TARGET="tests/vm"
        ;;
    modbus-mqtt-gateway)
        TARGET="tests/vm/test_modbus_mqtt_gateway.py"
        ;;
    mqtt-edge-historian)
        TARGET="tests/vm/test_mqtt_edge_historian.py"
        ;;
    opcua-mqtt-bridge)
        TARGET="tests/vm/test_opcua_mqtt_bridge.py"
        ;;
    *)
        echo "unknown app '${APP}'" >&2
        exit 1
        ;;
esac

if [[ ! -f "${IMAGE}" ]]; then
    echo "test image missing: ${IMAGE}" >&2
    echo "run tools/build-test-image.sh" >&2
    exit 1
fi
if [[ "${APP}" == "all" ]]; then
    for bundle in \
        "${BUNDLE_DIR}/modbus-mqtt-gateway.rugixb" \
        "${BUNDLE_DIR}/mqtt-edge-historian.rugixb" \
        "${BUNDLE_DIR}/opcua-mqtt-bridge.rugixb"; do
        if [[ ! -f "${bundle}" ]]; then
            echo "app bundle missing: ${bundle}" >&2
            echo "run tools/build-bundles.sh" >&2
            exit 1
        fi
    done
else
    bundle="${BUNDLE_DIR}/${APP}.rugixb"
    if [[ ! -f "${bundle}" ]]; then
        echo "app bundle missing: ${bundle}" >&2
        echo "run tools/build-bundles.sh" >&2
        exit 1
    fi
fi
if [[ ! -f "${KEY}" ]]; then
    echo "SSH key missing: ${KEY}" >&2
    echo "run tools/build-test-image.sh" >&2
    exit 1
fi

export RUGIX_TEST_IMAGE="${IMAGE}"
export RUGIX_BUNDLE_DIR="${BUNDLE_DIR}"
export RUGIX_TEST_SSH_KEY="${KEY}"

if command -v uv >/dev/null 2>&1; then
    (cd "${ROOT}" && uv run --no-project --with-editable "${TESTKIT}" --with pytest pytest "${TARGET}" -s)
else
    export PYTHONPATH="${TESTKIT}/src${PYTHONPATH:+:${PYTHONPATH}}"
    (cd "${ROOT}" && python3 -m pytest "${TARGET}" -s)
fi
