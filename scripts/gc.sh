#!/usr/bin/env bash
# Garbage Collection 통합 게이트: ruff + pytest + verify-docs + build
# 결과를 docs/harness/gc-history.md에 append.
#
# Usage: bash scripts/gc.sh [--skip-build] [--no-cov]

set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

SKIP_BUILD=0
NO_COV=0
for arg in "$@"; do
  case "$arg" in
    --skip-build) SKIP_BUILD=1 ;;
    --no-cov) NO_COV=1 ;;
  esac
done

STATUS=0
LOG=()

step() {
  local name="$1"; shift
  echo ""
  echo "━━ ${name} ━━"
  if "$@"; then
    LOG+=("PASS ${name}")
    return 0
  else
    LOG+=("FAIL ${name}")
    STATUS=1
    return 1
  fi
}

# Activate venv if present
if [ -f ".venv/bin/activate" ]; then
  # shellcheck source=/dev/null
  source .venv/bin/activate
fi

step "ruff check"      ruff check .
# ruff format은 프로젝트가 자체 스타일을 유지하므로 비차단(advisory). 신규 파일만 점검 권장.
ruff format --check . > /dev/null 2>&1 && LOG+=("PASS ruff format") || LOG+=("WARN ruff format (advisory)")

if [ "$NO_COV" -eq 1 ]; then
  step "pytest"        pytest -q
else
  step "pytest+cov"    pytest -q --cov=src/humax_excel_mcp --cov-report=term-missing --cov-fail-under=70
fi

step "vulture"         vulture --min-confidence 80 || echo "(vulture issues — non-blocking, review manually)"

# 성능 벤치마크 (advisory, 비차단): accuracy-speed PRD 벤치 게이트
pytest -q tests/benchmarks -m benchmark -p no:cacheprovider > /dev/null 2>&1 \
  && LOG+=("PASS benchmarks") || LOG+=("WARN benchmarks (advisory)")

step "verify-docs"     python scripts/verify_docs.py

if [ "$SKIP_BUILD" -eq 0 ]; then
  if python -c "import build" 2>/dev/null; then
    step "python -m build" python -m build --wheel --sdist
  else
    LOG+=("SKIP python -m build (build 미설치)")
  fi
fi

# Append to gc-history
TS=$(date +"%Y-%m-%d %H:%M:%S")
HISTORY="docs/harness/gc-history.md"
if [ -f "$HISTORY" ]; then
  if [ "$STATUS" -eq 0 ]; then
    RESULT="DONE"
  else
    RESULT="DONE_WITH_CONCERNS"
  fi
  printf "| %s | — | — | — | — | — | %s | gc.sh: %s |\n" \
    "$TS" "$RESULT" "${LOG[*]}" >> "$HISTORY"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━"
echo "GC 결과:"
for line in "${LOG[@]}"; do
  echo "  $line"
done
if [ "$STATUS" -eq 0 ]; then
  echo "→ PASS"
else
  echo "→ FAIL"
fi
exit $STATUS
