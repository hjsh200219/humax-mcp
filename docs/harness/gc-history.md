# gc-history.md

> Garbage Collection (품질 점검) 실행 이력. `scripts/gc.sh`가 자동 append.

| 일자 | 종합 점수 | Knowledge | Architecture | Quality | Adaptability | 상태 | 비고 |
|---|---|---|---|---|---|---|---|
| 2026-05-19 | 5.55 | 5.75 | 6.0 | 5.3 | 5.0 | DONE | harness-setup 초기 베이스라인 |
| 2026-05-19 22:50 | 63.75 / L3 | A=7.25 | B=6.0 | C=6.0 | D=6.0 | DONE_WITH_CONCERNS | GC #1 — 12원칙 채점 적용. 약점 Top3: P6 cov=4, P3 enforce=5, P7 gc-auto=5. 발견: TD-012 (15 함수 >50줄), TD-013 (progress.txt 잔존). verify-docs 4/4 PASS, 234 tests PASS, ruff PASS |
| 2026-05-19 22:56:41 | — | — | — | — | — | DONE_WITH_CONCERNS | gc.sh: PASS ruff check FAIL ruff format PASS pytest PASS vulture PASS verify-docs FAIL python -m build |
| 2026-05-19 22:58:42 | — | — | — | — | — | DONE | gc.sh: PASS ruff check WARN ruff format (advisory) PASS pytest PASS vulture PASS verify-docs |
| 2026-05-19 23:00 | **70.4 / L4** | A=7.25 | B=6.67 | C=7.33 | D=7.0 | DONE | GC #2 (manual scoring) — TD-001/002/003 해소. Coverage 88.70% (>70 게이트). vulture clean. pre-commit 설치. gc.sh 5/5 PASS. ΔGC#1: +6.65점. P6: 4→8, P3: 5→7, P7: 5→7. **L3 → L4 진입**. 약점 잔존: P5 disclosure (ADR 없음), P9 knowledge (용어집 없음) |
