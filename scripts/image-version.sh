#!/usr/bin/env sh
set -eu

SHA="${GITHUB_SHA:-$(git rev-parse --verify HEAD)}"
SHORT_SHA=$(printf '%s' "$SHA" | cut -c1-7)
STAMP=$(date -u +%Y%m%d.%H%M%S)

printf '%s-%s\n' "$STAMP" "$SHORT_SHA"
