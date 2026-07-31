# 휴맥스 Cash Forecast 경영진 대시보드 — 기획서

작성일: 2026-07-31 · 대상: 주간 Cash Forecast 경영진 보고
파이프라인: **Excel → Python 파서 → Supabase → Vercel(Next.js) → 경영진**

---

## 0. 확정된 결정사항

| 항목 | 결정 | 함의 |
|---|---|---|
| 접근 통제 | **Vercel 비밀번호 보호** | 대시보드는 로그인 게이트 뒤에만 노출. 인터넷 공개 금지 |
| 1차 범위 | **요약 대시보드 우선** | KPI 밴드 + 월별 차트 + 3대 활동 + 전주대비 하이라이트 |
| 데이터 저장 | **코드만 GitHub, 데이터는 Supabase** | `.xlsx`·스냅샷 JSON은 `.gitignore`. 숫자는 비공개 DB에만 |

---

## 1. 소스 데이터 구조 (Summary 시트)

두 주차 파일 모두 `Summary(MMDD)` 시트가 진실의 원천. 열 배치:

| 구간 | 열 | 의미 |
|---|---|---|
| 2024 실적 | C–N | 1~12월 (A=Actual) |
| 2025 실적 | O–Z | 1~12월 |
| **2026 전망** | **AA–AL** | 1~12월 ← 대시보드 핵심 |
| 이번 주 합계 | AM | 예: 7/31 연간 합 |
| 전주 합계 | AN | 예: 7/24 연간 합 |
| 전주대비 변동 | AO | AM − AN |

핵심 행:

| 행 | 계정 | 대시보드 용도 |
|---|---|---|
| 4 | 1. Beginning balance (총현금) | 기초 |
| 5 | 1) 영업활동 증감 | 워터폴 |
| 29 | 2) 투자활동 증감 | 워터폴 |
| 33 | 3) 재무활동 증감 | 워터폴 |
| 46 | 2. 종합수지 | KPI |
| 47 | 3. Ending balance | **KPI · 월별 라인차트** |
| 50 | 자금일보 기준 차입금 | KPI |
| 51 | 4. Net cash | KPI |
| 102–118 | 자산매각/조달 파이프라인 | 하단 카드 |

> 전주대비는 엑셀 AO열에 의존하지 않고 **Supabase에 누적된 주차 스냅샷 간 차이로 재계산**한다(확장성·감사추적).

### 이번 주(7/24→7/31) 검증된 인사이트
- 연간 종합수지 **−1.4억** (총량 유지)
- 영업활동: 7월 −13.5억 ↔ 8월 +18.1억 (시점 이동), 12월 −6.0억
- 투자·재무·차입금 **변동 없음**
- **2026 최저 유동성 = 12월 기말잔액 20.6억** ← 경영진 주목 포인트

---

## 2. Supabase 스키마

프로젝트: `vfwcftkeybehengyqoxy` (handshim1's Project) — 이미 링크됨.

```sql
-- 주차 메타
create table cf_snapshots (
  id           bigserial primary key,
  report_date  date not null unique,      -- 2026-07-31
  source_file  text,                       -- 원본 파일명
  created_at   timestamptz default now()
);

-- 정규화된 값 (long format)
create table cf_values (
  snapshot_id  bigint references cf_snapshots(id) on delete cascade,
  section      text not null,   -- 'operating'|'investing'|'financing'|'balance'|'debt'|'netcash'
  account      text not null,   -- '영업활동 증감' 등 (행 라벨)
  fiscal_year  int  not null,   -- 2024|2025|2026
  month        int  not null,   -- 1..12
  value        numeric,         -- 억원
  primary key (snapshot_id, account, fiscal_year, month)
);

-- 자산매각/조달 파이프라인
create table cf_pipeline (
  snapshot_id  bigint references cf_snapshots(id) on delete cascade,
  item         text,            -- 'TLT','HNW','스테이지파이브'...
  note         text             -- '26년 매각 목표' 등
);

-- RLS: 익명 읽기 금지, service_role 쓰기 / 인증사용자 읽기
alter table cf_values enable row level security;
```

전주대비 뷰:
```sql
create view cf_wow as
select cur.account, cur.fiscal_year, cur.month,
       cur.value                              as this_week,
       prev.value                             as last_week,
       cur.value - coalesce(prev.value,0)     as delta
from cf_values cur
join cf_snapshots s_cur on s_cur.id = cur.snapshot_id
left join lateral (
  select v.value from cf_values v
  join cf_snapshots s2 on s2.id = v.snapshot_id
  where s2.report_date < s_cur.report_date
    and v.account=cur.account and v.fiscal_year=cur.fiscal_year and v.month=cur.month
  order by s2.report_date desc limit 1
) prev on true;
```

---

## 3. 파서 (기존 Python 자산 재사용)

- 위치: `src/humax_excel_mcp/` 의 openpyxl 유틸 재사용, 신규 `scripts/ingest_cashflow.py`
- 입력: `휴맥스Cash forecast (YYYYMMDD).xlsx`
- 처리: `Summary(MMDD)` 시트 → 행/열 매핑(위 표) → long-format 레코드
- 출력: Supabase upsert (`cf_snapshots` → `cf_values` → `cf_pipeline`)
- 실행: `python scripts/ingest_cashflow.py "<xlsx경로>"`
- 시크릿: `SUPABASE_URL`, `SUPABASE_SERVICE_KEY` → `.env`(gitignore)

---

## 4. 대시보드 (1차 = 요약)

경영진 1페이지, 위→아래 스캔 순서:

1. **KPI 밴드** — 연말 기말잔액 / 최저 유동성 월 / 차입금 / Net cash, 각 **전주대비 ▲▼ 뱃지**
2. **월별 현금흐름 라인차트** — 2026 기말잔액 12개월 + 전주 라인 점선 오버레이, 최저점(12월) 강조
3. **3대 활동 워터폴** — 영업/투자/재무 → 종합수지
4. **전주대비 변동 테이블** — 변동 발생 계정·월만 하이라이트(7·8·12월)
5. **파이프라인 카드** — 자산매각/IPO/조달 (TLT, HNW, 스테이지파이브 등)

- 스택: **Next.js(App Router) + Recharts + Tailwind**, Supabase에서 서버사이드 조회
- 단위 표기: 억원, 부호/색상 일관(증가=녹, 감소=적)

---

## 5. Vercel 배포 + 비밀번호 보호

- 배포: GitHub `hjsh200219/humax-mcp` 연동 → Vercel 자동 빌드
- **비밀번호 보호 (택1)**
  - (A) Vercel **Password Protection** (Pro 플랜 프로젝트 설정, 코드 0줄)
  - (B) **Next.js middleware 게이트** — 단일 공유 비밀번호를 `DASHBOARD_PASSWORD` env로 검증하는 쿠키 세션(플랜 무관, 무료)
  - 기본 권장: 플랜에 따라 (A) 우선, 미지원 시 (B)
- env: `SUPABASE_URL`, `SUPABASE_ANON_KEY`(읽기전용 RLS), `DASHBOARD_PASSWORD`

---

## 6. 주간 운영 워크플로우

```
매주 금요일 새 xlsx 수신
  └─ python scripts/ingest_cashflow.py "<파일>"   # Supabase에 스냅샷 추가
       └─ Vercel 대시보드는 최신 스냅샷 자동 반영 (전주대비 자동 계산)
            └─ 경영진에 비밀번호 보호 링크 공유
```

---

## 7. 단계별 로드맵

- [ ] **Phase 1 — 파서 & 스키마**: `scripts/ingest_cashflow.py` + Supabase 테이블 생성, 7/24·7/31 두 주차 적재
- [ ] **Phase 2 — 대시보드**: Next.js 요약 페이지(KPI·차트·워터폴·전주대비·파이프라인)
- [ ] **Phase 3 — 배포/보안**: Vercel 연결 + 비밀번호 보호 + env 설정
- [ ] **Phase 4 — 운영화**: 주간 적재 스크립트 문서화, README 갱신

---

## 8. 보안 체크리스트

- [ ] `.gitignore` 에 `*.xlsx`, `.env`, `data/*.json` 추가 — 원본 숫자 커밋 차단
- [ ] Supabase RLS: 익명 접근 차단, 대시보드는 읽기전용 키 사용
- [ ] Vercel 비밀번호 보호 활성 확인 후에만 링크 공유
- [ ] GitHub 레포 공개 여부 확인 (public이면 데이터 관련 파일 이력까지 점검)
