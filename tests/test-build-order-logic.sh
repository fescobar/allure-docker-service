#!/usr/bin/env bash
# Regressão: último build de histórico só pode vir de pastas numéricas (não report-navigator.html).
set -euo pipefail

fail() { echo "FAIL: $*" >&2; exit 1; }

find_last_numeric() {
  local PROJECT_REPORTS="$1"
  local LAST_REPORT_DIRECTORY=""
  if [ -d "$PROJECT_REPORTS" ]; then
    LAST_REPORT_DIRECTORY=$(ls -1 "$PROJECT_REPORTS" 2>/dev/null | grep -E '^[0-9]+$' | sort -n | tail -1)
  fi
  echo "$LAST_REPORT_DIRECTORY"
}

compute_build_order() {
  local LAST="$1"
  if [[ -z "$LAST" ]]; then
    echo 1
  else
    echo $(("$LAST" + 1))
  fi
}

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

# Vazio -> próximo 1
R="$TMP/empty"
mkdir -p "$R"
L=$(find_last_numeric "$R")
[[ "$(compute_build_order "$L")" == "1" ]] || fail "vazio deveria dar BUILD_ORDER=1"

# Só latest + report-navigator.html (cenário do bug) -> ainda 1, sem erro de aritmética
R="$TMP/nav"
mkdir -p "$R/latest"
touch "$R/report-navigator.html"
L=$(find_last_numeric "$R")
[[ -z "$L" ]] || fail "sem pastas numéricas: LAST deveria ser vazio, veio '$L'"
[[ "$(compute_build_order "$L")" == "1" ]] || fail "sem numéricas: BUILD_ORDER deveria ser 1"

# Histórico 1,2,3 + arquivo recente -> último 3, próximo 4
R="$TMP/hist"
mkdir -p "$R/1" "$R/2" "$R/3"
touch "$R/report-navigator.html"
L=$(find_last_numeric "$R")
[[ "$L" == "3" ]] || fail "esperado último=3, veio '$L'"
[[ "$(compute_build_order "$L")" == "4" ]] || fail "esperado BUILD_ORDER=4"

echo "OK: test-build-order-logic.sh"
