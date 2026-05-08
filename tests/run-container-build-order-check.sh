#!/usr/bin/env bash
# Roda dentro da imagem local: pastas 1,2 + report-navigator.html -> último=2, próximo=3
set -euo pipefail
IMAGE="${1:-allure-docker-service:local-test}"
docker run --rm "$IMAGE" /bin/sh <<'EOS'
STATIC_CONTENT_PROJECTS=/app/allure-docker-api/static/projects
mkdir -p "$STATIC_CONTENT_PROJECTS/tproj/reports/latest"
touch "$STATIC_CONTENT_PROJECTS/tproj/reports/report-navigator.html"
mkdir -p "$STATIC_CONTENT_PROJECTS/tproj/reports/1" "$STATIC_CONTENT_PROJECTS/tproj/reports/2"
LAST=$(ls -1 "$STATIC_CONTENT_PROJECTS/tproj/reports" | grep -E '^[0-9]+$' | sort -n | tail -1)
NEXT=$((LAST + 1))
echo "LAST=$LAST NEXT=$NEXT"
test "$LAST" = "2" && test "$NEXT" = "3"
EOS
echo "OK: container build-order smoke check"
