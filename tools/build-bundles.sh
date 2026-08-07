#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUNDLER="${RUGIX_BUNDLER:-rugix-bundler}"
DIST_DIR="${RUGIX_DIST_DIR:-"${ROOT}/dist"}"
PLATFORM="${RUGIX_PLATFORM:-linux/amd64}"
NO_IMAGES=false
SKIP_BUILD=false
ONLY_EXAMPLE=""

usage() {
    cat <<'EOF'
Usage: tools/build-bundles.sh [OPTIONS]

Options:
  --example NAME      Build one example.
  --platform VALUE    Image platform for Docker builds/pulls, default linux/amd64.
  --no-images         Pack bundles without container image payloads.
  --skip-build        Do not run tools/docker-build.sh first.
  -h, --help          Show this help.
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --example) ONLY_EXAMPLE="$2"; shift 2 ;;
        --platform) PLATFORM="$2"; shift 2 ;;
        --no-images) NO_IMAGES=true; shift ;;
        --skip-build) SKIP_BUILD=true; shift ;;
        -h|--help) usage; exit 0 ;;
        *) echo "unknown argument: $1" >&2; usage >&2; exit 1 ;;
    esac
done

if ! command -v "${BUNDLER}" >/dev/null 2>&1; then
    echo "rugix-bundler not found: ${BUNDLER}" >&2
    echo "run mise install or set RUGIX_BUNDLER" >&2
    exit 1
fi

if ! command -v docker >/dev/null 2>&1 && [[ "${NO_IMAGES}" != true ]]; then
    echo "docker is required unless --no-images is used" >&2
    exit 1
fi

mkdir -p "${DIST_DIR}"

mapfile -t example_dirs < <(find "${ROOT}/examples" -mindepth 1 -maxdepth 1 -type d ! -name "_*" | sort)
if [[ -n "${ONLY_EXAMPLE}" ]]; then
    example_dirs=("${ROOT}/examples/${ONLY_EXAMPLE}")
fi

for example_dir in "${example_dirs[@]}"; do
    name="$(basename "${example_dir}")"
    compose="${example_dir}/docker-compose.yml"
    metadata="${example_dir}/app-meta.json"
    output="${DIST_DIR}/${name}.rugixb"

    if [[ ! -f "${compose}" ]]; then
        echo "missing compose file for ${name}: ${compose}" >&2
        exit 1
    fi
    if [[ ! -f "${metadata}" ]]; then
        echo "missing metadata file for ${name}: ${metadata}" >&2
        exit 1
    fi

    echo "building ${name}"

    if [[ "${SKIP_BUILD}" != true && "${NO_IMAGES}" != true ]]; then
        "${ROOT}/tools/docker-build.sh" --platform "${PLATFORM}" --example "${name}"
    fi

    cmd=(
        "${BUNDLER}"
        apps pack docker-compose
        --app "${name}"
        --health-check-timeout 180
        --metadata-file app-meta.json
    )

    if [[ "${NO_IMAGES}" == true ]]; then
        cmd+=(--disable-image-bundling --disable-pinning)
    else
        cmd+=(--platform "${PLATFORM}")
    fi
    if [[ -d "${example_dir}/config" ]]; then
        cmd+=(--include config)
    fi

    cmd+=(docker-compose.yml "${output}")

    (cd "${example_dir}" && "${cmd[@]}")
    echo "wrote ${output}"
done
