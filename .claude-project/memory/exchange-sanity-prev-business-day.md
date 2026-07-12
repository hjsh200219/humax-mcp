---
name: exchange-sanity-prev-business-day
description: exchange sanity check는 세션 내 _rates_by_date 저장소 기반 전영업일 비교 — 같은 날짜 키 비교는 dead code
type: project
created: 2026-07-12
---

get_exchange_rates의 기존 sanity check는 **같은 날짜 키로 자기 자신과 비교하는 dead code**였다 — 코드는 존재하지만 감지 0건.

교체 구현 (`src/humax_excel_mcp/tools/exchange.py`):
- 세션(프로세스) 스코프 저장소 `_rates_by_date: dict[날짜, dict[통화, 매매기준율]]`에 모든 조회 결과 적재.
- sanity: 직전 영업일(D-1부터 역순 탐색) 데이터가 저장소에 있으면 매매기준율 20% 초과 변동 시 `sanity_warning=True`. 없으면 skip (에러 아님).
- 휴일 fallback: D-1..D-7 **asyncio.gather 병렬 조회** 후 최근접 영업일 채택. 병렬 조회의 부수 응답도 전부 `_rates_by_date`에 적재 → 추가 API 호출 없이 sanity 비교 데이터 확보.

**Why:** 시계열 비교 검증은 "비교 대상 데이터를 어디서 얻는가"가 설계의 전부다. 비교 대상 확보 경로가 없으면 sanity check는 형태만 남은 dead code가 된다. fallback 병렬 조회의 부산물 재활용이 그 확보 경로.

**How to apply:**
- 이상치 감지 로직 추가 시 baseline 데이터의 출처·수명(세션 스코프)을 먼저 명시.
- 병렬 fallback의 실패하지 않은 부수 응답은 버리지 말고 저장소에 적재.
- 프로세스 재시작 후 첫 조회는 비교 대상이 없어 sanity skip — 정상 동작임을 인지.

**관련:** [[pytest-httpx-036-api]] (병렬 fallback 테스트 방법)
