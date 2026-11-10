#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VM_DIR="${ROOT}/vm"
BAKERY="${RUGIX_BAKERY:-"${VM_DIR}/run-bakery"}"
SYSTEM="${RUGIX_TEST_SYSTEM:-apps-test-amd64}"
BAKERY_OUTPUT="${VM_DIR}/build/${SYSTEM}/system.img"
OUTPUT="${RUGIX_TEST_IMAGE:-"${BAKERY_OUTPUT}"}"
KEY="${RUGIX_TEST_SSH_KEY:-"${VM_DIR}/ssh/id_ed25519"}"
PARAM_FILE="${VM_DIR}/ssh/params.toml"
PARAM_FILE_ARG="${PARAM_FILE#"${VM_DIR}/"}"

if [[ ! -x "${BAKERY}" && ! -x "$(command -v "${BAKERY}" 2>/dev/null || true)" ]]; then
    echo "Rugix Bakery runner not found. Set RUGIX_BAKERY or use ${VM_DIR}/run-bakery." >&2
    exit 1
fi

mkdir -p "$(dirname "${KEY}")" "$(dirname "${OUTPUT}")"

if [[ ! -f "${KEY}" ]]; then
    ssh-keygen -t ed25519 -N "" -f "${KEY}" -C "rugix-apps-examples-test" >/dev/null
fi

public_key="$(cat "${KEY}.pub")"
cat > "${PARAM_FILE}" <<EOF
["ssh"]
root_authorized_keys = """
${public_key}
"""
EOF

(cd "${VM_DIR}" && "${BAKERY}" bake image --param-file "${PARAM_FILE_ARG}" "${SYSTEM}")
if [[ "${OUTPUT}" != "${BAKERY_OUTPUT}" ]]; then
    cp "${BAKERY_OUTPUT}" "${OUTPUT}"
fi
echo "wrote ${OUTPUT}"
echo "ssh key ${KEY}"
