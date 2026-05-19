#!/usr/bin/env python3
"""verify-docs: 문서-코드 동기화 검증.

게이트:
- 도구 수 일치: tools/__init__.TOOL_NAMES vs AGENTS.md 도구 표
- 스키마 버전 일치: bp26/raw_bp26.SCHEMA_VERSION vs docs/generated/schema-snapshot.md
- 레이어 import 방향: L3 → L2 역참조 차단, L2 ↔ L2 횡참조 차단, L5 외부 의존 차단
- 진입 문서 라인 한도: AGENTS.md ≤ 120

Exit 0 통과, 1 실패. 게이트 메시지는 한국어.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "humax_excel_mcp"

AGENTS_MD = ROOT / "AGENTS.md"
SCHEMA_SNAPSHOT = ROOT / "docs" / "generated" / "schema-snapshot.md"


def fail(msg: str) -> None:
    print(f"[FAIL] {msg}", file=sys.stderr)


def ok(msg: str) -> None:
    print(f"[OK]   {msg}")


def check_tool_count() -> bool:
    sys.path.insert(0, str(ROOT / "src"))
    try:
        from humax_excel_mcp.tools import TOOL_NAMES  # type: ignore[import-not-found]
    except Exception as exc:  # pragma: no cover
        fail(f"TOOL_NAMES import 실패: {exc}")
        return False

    code_count = len(TOOL_NAMES)
    text = AGENTS_MD.read_text(encoding="utf-8")
    doc_count = len(re.findall(r"^\| \d+ \|", text, flags=re.MULTILINE))

    if code_count != doc_count:
        fail(f"도구 수 불일치: code={code_count}, AGENTS.md={doc_count}")
        return False
    ok(f"도구 수 일치: {code_count}")
    return True


def check_schema_version() -> bool:
    sys.path.insert(0, str(ROOT / "src"))
    try:
        from humax_excel_mcp.schemas import bp26, raw_bp26  # type: ignore[import-not-found]
    except Exception as exc:  # pragma: no cover
        fail(f"schema import 실패: {exc}")
        return False

    snap = SCHEMA_SNAPSHOT.read_text(encoding="utf-8") if SCHEMA_SNAPSHOT.exists() else ""
    failures: list[str] = []
    if bp26.SCHEMA_VERSION not in snap:
        failures.append(f"bp26.SCHEMA_VERSION={bp26.SCHEMA_VERSION} not in schema-snapshot.md")
    if raw_bp26.SCHEMA_VERSION not in snap:
        failures.append(
            f"raw_bp26.SCHEMA_VERSION={raw_bp26.SCHEMA_VERSION} not in schema-snapshot.md"
        )
    if failures:
        for f in failures:
            fail(f)
        return False
    ok(f"스키마 버전 일치: bp26={bp26.SCHEMA_VERSION}, raw_bp26={raw_bp26.SCHEMA_VERSION}")
    return True


def check_layer_imports() -> bool:
    violations: list[str] = []

    # L3 (core) → L2 (tools) 역방향
    for py in (SRC / "core").rglob("*.py"):
        text = py.read_text(encoding="utf-8")
        if re.search(r"from \.\.tools", text):
            violations.append(f"L3→L2 역방향: {py.relative_to(ROOT)}")

    # L2 (tools) ↔ L2 횡방향
    # 허용:
    #   - __init__.py (register용)
    #   - report.py (PRD §4.10 / US-017 명시적 orchestrator: apply_golden_template + verify_sums 조합)
    L2_ORCHESTRATOR_ALLOWLIST = {"__init__.py", "report.py"}
    for py in (SRC / "tools").rglob("*.py"):
        if py.name in L2_ORCHESTRATOR_ALLOWLIST:
            continue
        text = py.read_text(encoding="utf-8")
        for m in re.finditer(r"^from \.([a-z_][a-z_0-9]*) import", text, flags=re.MULTILINE):
            other = m.group(1)
            if other and other != "__init__":
                violations.append(f"L2↔L2 횡참조: {py.relative_to(ROOT)} -> tools/{other}.py")

    # L5 (schemas) 외부 humax_excel_mcp 의존 차단
    for py in (SRC / "schemas").rglob("*.py"):
        text = py.read_text(encoding="utf-8")
        if re.search(r"from \.\.[a-z]", text):
            violations.append(f"L5 외부 의존: {py.relative_to(ROOT)}")

    if violations:
        for v in violations:
            fail(v)
        return False
    ok("레이어 import 방향 준수")
    return True


def check_agents_md_size() -> bool:
    text = AGENTS_MD.read_text(encoding="utf-8")
    lines = text.count("\n") + 1
    limit = 120
    if lines > limit:
        fail(f"AGENTS.md 라인 한도 초과: {lines} > {limit}")
        return False
    ok(f"AGENTS.md 크기: {lines} lines (≤ {limit})")
    return True


def main() -> int:
    checks = [
        check_tool_count,
        check_schema_version,
        check_layer_imports,
        check_agents_md_size,
    ]
    results = [c() for c in checks]
    if all(results):
        print("\n→ verify-docs: PASS")
        return 0
    print(f"\n→ verify-docs: FAIL ({results.count(False)}/{len(results)} checks failed)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
