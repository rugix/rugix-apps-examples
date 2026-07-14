#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PODMAN="${PODMAN:-podman}"
PLATFORM="${RUGIX_PLATFORM:-linux/amd64}"
ONLY_EXAMPLE=""

usage() {
    cat <<'EOF'
Usage: tools/podman-build.sh [OPTIONS]

Options:
  --example NAME      Build one example.
  --platform VALUE    Image platform, default linux/amd64.
  -h, --help          Show this help.
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --example) ONLY_EXAMPLE="$2"; shift 2 ;;
        --platform) PLATFORM="$2"; shift 2 ;;
        -h|--help) usage; exit 0 ;;
        *) echo "unknown argument: $1" >&2; usage >&2; exit 1 ;;
    esac
done

if ! command -v "${PODMAN}" >/dev/null 2>&1; then
    echo "podman is required; set PODMAN to override the binary" >&2
    exit 1
fi

mapfile -t example_dirs < <(find "${ROOT}/examples" -mindepth 1 -maxdepth 1 -type d ! -name "_*" | sort)
if [[ -n "${ONLY_EXAMPLE}" ]]; then
    example_dirs=("${ROOT}/examples/${ONLY_EXAMPLE}")
fi

for example_dir in "${example_dirs[@]}"; do
    name="$(basename "${example_dir}")"
    manifest="${example_dir}/images.txt"
    if [[ ! -f "${manifest}" ]]; then
        echo "missing image manifest for ${name}: ${manifest}" >&2
        exit 1
    fi

    echo "preparing images for ${name}"
    while read -r action image context; do
        [[ -z "${action}" || "${action}" == \#* ]] && continue
        case "${action}" in
            pull)
                echo "pull ${image}"
                "${PODMAN}" pull --platform "${PLATFORM}" "${image}"
                ;;
            build)
                if [[ -z "${context:-}" ]]; then
                    echo "missing build context for ${image}" >&2
                    exit 1
                fi
                echo "build ${image}"
                "${PODMAN}" build --platform "${PLATFORM}" -t "${image}" "${example_dir}/${context}"
                ;;
            *)
                echo "unknown image action '${action}' in ${manifest}" >&2
                exit 1
                ;;
        esac
    done < "${manifest}"
done

