# PRD — 정확도·속도 개선 (Accuracy & Speed Improvement)

> Rev 2 (2026-07-12, 구현 완료). SSOT: 본 문서. 관련: [mcp-design-plan.md](./mcp-design-plan.md) · [tech-debt-tracker.md](../exec-plans/tech-debt-tracker.md) (TD-006, TD-007 해소)
>
> 구현 편차 (Rev 2):
> - US-A2: 직전 영업일 데이터 부재 시 "API 1회 추가 조회" 대신 **세션 내 저장소 조회 전용**으로 확정 — fallback 병렬 조회·과거 날짜 조회 결과가 `_rates_by_date`에 적재되므로 세션에서 이전 영업일을 본 적 있으면 비교, 없으면 skip. 추가 API 쿼터 소모 0, 본 응답 지연 0.
> - US-S2: openpyxl 구조상 values/formulas 단일 로드 불가 → 양쪽 `read_only=True` 전환 + values 경로는 워크북 캐시 공유로 절충.
> - US-S3: diff 도구는 시트 fallback 로직 특수성으로 캐시 미적용 (extract/verify/allocation_get 적용).

## 1. 배경

v0.1.x에서 10개 도구 + 234 테스트 + 커버리지 88.7% 확보. 그러나 코드 감사 결과
**"검증했다고 보고하지만 실제로는 검증하지 않는" 정확도 결함**과
**동일 파일 반복 파싱·이벤트루프 블로킹 등 구조적 속도 낭비**가 확인됨.
결산 도구 특성상 정확도 결함은 조용한 오보고(silent false-PASS)로 이어지므로 속도보다 우선.

## 2. 목표

| 축 | 지표 | 현재 | 목표 |
|---|---|---|---|
| 정확도 | verify_sums 실제 검증 계층 수 | 1/5 (총합계만) | 5/5 (전 계층 rollup 대조) |
| 정확도 | 환율 전일 대비 급변(>20%) 감지 | 미동작 (dead code) | 동작 + 테스트 증명 |
| 정확도 | 수식 검사 실패 시 신호 | 침묵 (`except: pass`) | 경고 필드로 표면화 |
| 속도 | verify_sums 파일 로드 횟수 | 2회 전체 파싱 | 1회 (values+formulas 단일 패스) 또는 read_only 2회 |
| 속도 | 세션 내 동일 파일 재파싱 | 도구 호출마다 | mtime+size 키 캐시 히트 시 0회 |
| 속도 | get_exchange_rates 휴일 fallback 최악 지연 | ~80s (10s × 8 동기 호출) | ≤15s (async + 병렬 조회) |
| 회귀 방지 | 성능 벤치마크 게이트 | 없음 | `gc.sh` 벤치 단계 + 임계치 |

## 3. 현황 진단 (근거)

### 3.1 정확도 결함

| ID | 심각도 | 위치 | 문제 |
|---|---|---|---|
| A-1 | **P0** | `tools/verify.py:78-85` | 총합계 외 계층(사업부/대조직/중조직/소조직)은 `expected=actual, difference=0.0, status="PASS"` 고정. 5계층 검증을 표방하나 실제 대조는 총합계 1개뿐. 중간 계층 소계 오류가 무조건 PASS로 보고됨 |
| A-2 | **P0** | `tools/exchange.py:119-133` | `_apply_sanity`가 `_prev_day_cache[date]`를 **같은 날짜 키**로 조회 → 첫 호출은 저장만, 같은 날 재호출은 캐시 히트로 아예 미실행. 전일 대비 급변 감지가 구조적으로 불가능한 dead code |
| A-3 | P1 | `tools/verify.py:134-135` | 수식 검사 전체가 `except Exception: pass`. 파일 문제로 검사 실패해도 `warnings=0`으로 정상 보고 |
| A-4 | P1 | `core/aggregator.py:212` | EVCS 배부율 곱셈(`amount × rate / 100`)의 float 오차 정책 부재. 반올림 시점·단위(원 단위 절사 여부) 미정의 → 합계 검증 tolerance와 상호작용 시 위양성 가능 |
| A-5 | P2 | `core/excel_io.py:58` | `_count_schema_matches`의 `if str(cell) if str(cell) in keys` — `str(None)`이 truthy로 통과하는 취약한 표현. 헤더 오탐 시 min-match=5 고정 임계와 결합해 자동감지 오류 여지 |
| A-6 | P2 | `core/aggregator.py:150-151` | 파싱 실패 월 행 silent drop. `month_parse_failed` 메타데이터만 기록 — 임계 초과 시 경고/실패 정책 없음 |

### 3.2 속도 낭비

| ID | 심각도 | 위치 | 문제 |
|---|---|---|---|
| S-1 | **P1** | `tools/exchange.py:80-101` | async 함수 내부에서 동기 `httpx.Client` 사용 → MCP 서버 이벤트루프 블로킹. 휴일 fallback 시 최대 8회 순차 호출 = 최악 80초 동안 서버 전체 정지 |
| S-2 | **P1** | `tools/verify.py:37,111` | 동일 파일을 `data_only=True`/`False`로 2회 전체 로드. 두 로드 모두 `read_only=False` (TD-006) |
| S-3 | P1 | 전 read 도구 | 워크북/DataFrame 캐시 부재. extract → verify → diff 순 호출 시 같은 xlsx를 매번 재파싱. 대용량 raw에서 도구당 수 초씩 중복 |
| S-4 | P2 | `core/token_guard.py:64-66` | `auto_truncate` while 루프가 반복마다 전체 rows를 `json.dumps` 재직렬화 — O(n²)성 낭비 |
| S-5 | P2 | `core/excel_io.py:95` | `list(ws.iter_rows())` 전체 실체화 후 DataFrame 변환. 필터 조건이 있어도 전 행 로드 (TD-007 페이지네이션 부재와 결합) |
| S-6 | P2 | `tools/extract.py:83-86` | `astype(str).apply(lambda ...)` 행 단위 람다 — vectorized `str.contains` 계열로 대체 가능 |

## 4. 개선 항목

### Phase 1 — 정확도 P0 (조용한 오보고 제거)

**US-A1: verify_sums 실계층 rollup 검증**
- 소조직 상세를 org_l1/l2/l3 트리로 그룹핑, 각 상위 계층 행의 기재값 vs 하위 합산값 대조.
- 계층 구조 인식 불가 시 `PASS` 위장 대신 `SKIPPED` 상태 신설 (schemas/responses.py `LevelResult.status`에 추가).
- AC: 중간 계층 소계를 의도적으로 1원 틀어놓은 fixture에서 해당 계층 FAIL. 기존 PASS fixture 전체 회귀 없음.

**US-A2: 환율 sanity check 실동작화**
- `_prev_day_cache`를 날짜별 저장 유지하되, 비교 대상을 **직전 영업일**(fallback 로직 재사용) 데이터로 변경. 직전일 데이터 없으면 API 1회 추가 조회 후 캐시.
- AC: 전일 대비 +25% 조작 mock에서 `sanity_warning=True`. 같은 날 재호출 캐시 경로에서도 경고 유지.

**US-A3: 수식 검사 침묵 실패 제거**
- `except Exception: pass` → 에러를 `metadata.formula_check_error`로 표면화 + `summary.warnings`에 반영.
- AC: 손상 파일 mock에서 warnings ≥ 1, 에러 메시지 포함.

### Phase 2 — 속도 P1 (구조적 낭비 제거)

**US-S1: exchange async 전환**
- `httpx.AsyncClient` + fallback 7일 조회를 순차 대신 병렬(gather) 또는 짧은 타임아웃 순차로 전환. 재시도 정책 명시 (timeout 5s, 총 예산 15s).
- AC: 이벤트루프 블로킹 없음 (asyncio 테스트로 동시 도구 호출 검증). 휴일 fallback e2e mock ≤ 15s.

**US-S2: verify_sums 단일 로드**
- `read_only=True` 적용 + values/formulas 로드 통합 검토: openpyxl은 data_only 동시 제공 불가하므로 ① formulas 로드 1회에서 캐시된 값 시트(`wb_values`) 대체 가능성 벤치마크, 불가 시 ② 양쪽 모두 read_only 전환으로 절충.
- AC: 대용량 fixture(1만 행) 기준 wall-time 30%+ 단축 벤치 증빙.

**US-S3: 세션 워크북 캐시 (core/workbook_cache.py 신설, L3)**
- 키: `(path, mtime_ns, size)`. 값: parsed DataFrame. 파일 변경 시 자동 무효화. write/restore 도구는 저장 후 해당 path 캐시 invalidate.
- 안전 정책 P1(원본 보존)과 충돌 없음 — read 경로 전용.
- AC: extract 2회 연속 호출 시 2번째 로드 0회 (audit 로그 or 카운터로 증명). write 후 재호출 시 fresh 파싱.

### Phase 3 — 정밀도·잔여 최적화 P2

- **US-A4**: 금액 반올림 정책 SSOT 정의 (원 단위, round-half-even) → aggregator/verify tolerance 문서화 + 테스트.
- **US-A5**: `_count_schema_matches` 표현 정리 + None 명시 제외. 자동감지 실패 케이스 property test.
- **US-A6**: `month_parse_failed / input_rows > 1%` 시 응답에 경고 필드.
- **US-S4**: `auto_truncate` 이진 탐색 or 증분 크기 추정으로 재직렬화 제거.
- **US-S5**: TD-007 페이지네이션 (`page`/`page_size`) — extract에 사전 절단 도입.
- **US-S6**: extract 필터 vectorize.

### 벤치마크 게이트 (전 Phase 공통)

- `tests/benchmarks/` 신설: pytest-benchmark로 extract/verify/aggregate 대표 시나리오 측정.
- `scripts/gc.sh`에 벤치 단계 추가 (임계치 초과 시 경고, 초기엔 non-blocking).
- baseline 수치를 본 문서 §7에 기록 후 Phase별 갱신.

## 5. 비범위 (Non-Goals)

- 도구 신설·시그니처 변경 (기존 10개 도구 파라미터 호환 유지)
- LLM 측 프롬프트/클라이언트 최적화
- xlsx 외 포맷 지원, DB 도입

## 6. 실행 원칙

- TDD: 각 US는 실패 테스트 선행 (A-1, A-2는 현재 결함을 증명하는 red 테스트부터).
- 레이어 준수: 캐시는 L3(`core/`), 응답 필드 추가는 L5(`schemas/`) 선행.
- 에러/경고 코드는 `core/errors.py` `_make(CODE)` 등록 후 사용.
- Phase 완료마다 `bash scripts/gc.sh` 통과 + tech-debt-tracker 갱신 (TD-006/007 해소 반영).

## 7. 성공 지표 & Baseline (2026-07-12 구현 완료 실측)

| 측정 | 결과 | 판정 |
|---|---|---|
| extract cold → warm (1,008행 fixture) | 84ms → 6ms (캐시 히트, 재파싱 0회) | ✅ |
| verify_sums 5계층 실검증 (1,008행) | 175ms, 5/5 계층 (소계 없으면 SKIPPED) | ✅ |
| aggregate 7,200행 | 18ms | ✅ |
| 휴일 환율 fallback | D-1..D-7 병렬 gather, timeout 5s → 최악 ~5s | ✅ (≤15s) |
| 오보고 결함 red 테스트 | A-1 4건 / A-2 2건 / A-3 1건 → 전부 green | ✅ |

> 벤치 재측정: `pytest -s tests/benchmarks -m benchmark`. gc.sh advisory 단계 포함.

## 8. 리스크

| 리스크 | 완화 |
|---|---|
| rollup 검증 강화로 기존 실데이터가 FAIL 다발 | tolerance 파라미터 유지 + `SKIPPED` 상태로 점진 도입, 첫 릴리스는 경고 모드 옵션 |
| 워크북 캐시 stale 데이터 | mtime_ns+size 이중 키 + write 도구 명시 invalidate + e2e 테스트 |
| read_only 전환 시 openpyxl 동작 차이 (merged cell 등) | 도구별 벤치+회귀 테스트 후 개별 적용 (TD-006 조치와 동일 절차) |
| async 전환 중 기존 sync 테스트 파손 | `_fetch` 시그니처 유지한 어댑터 단계 거쳐 마이그레이션 |

## 9. 마일스톤

| Phase | 내용 | 산출물 |
|---|---|---|
| 1 | A-1, A-2, A-3 | 오보고 제거 + red→green 테스트, minor 버전 |
| 2 | S-1, S-2, S-3 + 벤치 게이트 | 벤치 baseline·개선 수치, TD-006 해소 |
| 3 | P2 잔여 (A-4~6, S-4~6) | TD-007 해소, tracker 정리 |
