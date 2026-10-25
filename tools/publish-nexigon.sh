#!/usr/bin/env bash
#
# Publish the app bundles of a release to a Nexigon repository.
#
# Every app is a package of the same name, which must exist. The release becomes
# a version of each package with the release tag as locked tag, and the floating
# tag `latest` moves to it. The bundles are attached with their hashes as
# `rugix.bundleHash` metadata. Running the script again for the same release
# only attaches missing bundles.
#
# Environment:
#   NEXIGON_REPOSITORY   Repository to publish to (required).
#   RELEASE_TAG          Git tag of the release (required).
#   DIST_DIR             Directory with the release assets (default: dist).
#   NEXIGON_CLI          Nexigon CLI executable (default: nexigon-cli).
#   NEXIGON_CLI_CONFIG   Nexigon CLI configuration file (optional).
#   SOURCE_COMMIT        Commit of the release (default: HEAD).

set -euo pipefail

DIST_DIR=${DIST_DIR:-dist}
NEXIGON_CLI=${NEXIGON_CLI:-nexigon-cli}
ARCHES=(x86_64 aarch64)

require_variable() {
    if [ -z "${!1:-}" ]; then
        echo "[ERROR] $1 is not set" >&2
        exit 1
    fi
}

run_cli() {
    if [ -n "${NEXIGON_CLI_CONFIG:-}" ]; then
        "${NEXIGON_CLI}" --config "${NEXIGON_CLI_CONFIG}" "$@"
    else
        "${NEXIGON_CLI}" "$@"
    fi
}

# Names of the apps with bundles in the release.
release_apps() {
    local bundle name
    for bundle in "${DIST_DIR}"/*-"${ARCHES[0]}".rugixb; do
        [ -e "${bundle}" ] || continue
        name=$(basename "${bundle}")
        printf '%s\n' "${name%-"${ARCHES[0]}".rugixb}"
    done
}

# Check that every app has a bundle and a hash for every architecture.
validate_app() {
    local app="$1" arch bundle
    for arch in "${ARCHES[@]}"; do
        bundle="${DIST_DIR}/${app}-${arch}.rugixb"
        if [ ! -f "${bundle}" ] || [ ! -s "${bundle}-hash" ]; then
            echo "[ERROR] '${bundle}' or its hash file is missing" >&2
            exit 1
        fi
    done
}

require_package() {
    local app="$1" count
    count=$(run_cli repositories packages list "${NEXIGON_REPOSITORY}" \
        | jq -er --arg name "${app}" '[.packages[] | select(.name == $name)] | length')
    if [ "${count}" != 1 ]; then
        echo "[ERROR] package '${NEXIGON_REPOSITORY}/${app}' does not exist" >&2
        exit 1
    fi
}

resolve_or_create_version() {
    local package_path="${NEXIGON_REPOSITORY}/$1" version_info metadata
    version_info=$(run_cli repositories versions resolve "${package_path}/${RELEASE_TAG}")
    case "$(jq -er '.result' <<<"${version_info}")" in
        Found)
            jq -er '.versionId' <<<"${version_info}"
            ;;
        NotFound)
            metadata=$(jq -nc --arg commit "${SOURCE_COMMIT}" '{sourceCommit: $commit}')
            run_cli repositories versions create "${package_path}" \
                --tag "${RELEASE_TAG},locked" \
                --metadata "${metadata}" \
                | jq -er '.versionId'
            ;;
        *)
            echo "[ERROR] unable to resolve '${package_path}/${RELEASE_TAG}'" >&2
            exit 1
            ;;
    esac
}

attach_bundles() {
    local app="$1" version_id="$2" attached arch filename bundle_hash asset_id
    attached=$(run_cli repositories versions info "${version_id}" | jq -r '.assets[]?.filename')
    for arch in "${ARCHES[@]}"; do
        filename="${app}-${arch}.rugixb"
        if grep -qxF "${filename}" <<<"${attached}"; then
            echo "[INFO] '${filename}' is already attached"
            continue
        fi
        bundle_hash=$(tr -d '\r\n' <"${DIST_DIR}/${filename}-hash")
        echo "[INFO] uploading '${filename}'"
        asset_id=$(run_cli repositories assets upload "${NEXIGON_REPOSITORY}" \
            "${DIST_DIR}/${filename}" | jq -er '.assetId')
        run_cli repositories versions assets add "${version_id}" "${asset_id}" "${filename}" \
            --metadata "$(jq -nc --arg hash "${bundle_hash}" '{rugix: {bundleHash: $hash}}')" \
            >/dev/null
    done
}

require_variable NEXIGON_REPOSITORY
require_variable RELEASE_TAG
SOURCE_COMMIT=${SOURCE_COMMIT:-$(git rev-parse HEAD)}

mapfile -t apps < <(release_apps)
if [ "${#apps[@]}" -eq 0 ]; then
    echo "[ERROR] no app bundles found in '${DIST_DIR}'" >&2
    exit 1
fi
# Check everything before changing the repository.
for app in "${apps[@]}"; do
    validate_app "${app}"
    require_package "${app}"
done

for app in "${apps[@]}"; do
    version_id=$(resolve_or_create_version "${app}")
    attach_bundles "${app}" "${version_id}"
    run_cli repositories versions tag "${version_id}" --tag latest,reassign >/dev/null
    echo "[INFO] published '${app}' ${RELEASE_TAG} to '${NEXIGON_REPOSITORY}/${app}'"
done
