#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
: "${ARCH:?ARCH is required}"
bundler="${RUGIX_BUNDLER:-rugix-bundler}"
shopt -s nullglob
bundles=(build/"$ARCH"/*.rugixb)
if [ "${#bundles[@]}" -eq 0 ]; then
    echo "No app bundles found for $ARCH" >&2
    exit 1
fi
mkdir -p dist
for bundle in "${bundles[@]}"; do
    name="$(basename "$bundle" .rugixb)"
    output="dist/${name}-${ARCH}.rugixb"
    mv "$bundle" "$output"
    "$bundler" hash "$output" > "$output-hash"
done
