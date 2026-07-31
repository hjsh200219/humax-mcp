-- ============================================================================
-- 휴맥스 Cash Forecast 경영진 대시보드 — 스키마
-- 주차별 스냅샷을 누적 저장하고, 전주 대비 변동을 뷰에서 계산한다.
-- 원본 엑셀 숫자는 GitHub에 저장하지 않으며 이 DB(비공개)에만 적재된다.
-- ============================================================================

-- 주차 메타 (한 주 = 한 스냅샷)
create table if not exists public.cf_snapshots (
  id           bigint generated always as identity primary key,
  report_date  date not null unique,          -- 보고 기준일 (예: 2026-07-31)
  source_file  text,                            -- 원본 파일명 (감사용)
  created_at   timestamptz not null default now()
);

-- Summary 시트 값 (대시보드 KPI·차트의 원천) — long format
-- section: beginning|operating|investing|financing|net|ending|debt|netcash|liquidity|sub
create table if not exists public.cf_summary (
  snapshot_id  bigint not null references public.cf_snapshots(id) on delete cascade,
  section      text   not null,
  account      text   not null,                 -- 행 라벨 (예: '영업활동 증감')
  fiscal_year  int    not null,                 -- 2024 | 2025 | 2026
  month        int    not null check (month between 1 and 12),
  value        numeric,                          -- 억원
  primary key (snapshot_id, account, fiscal_year, month)
);

-- 2026_CF 상세 라인아이템 + 셀 메모 (전주 대비 '변동 사유'의 원천)
-- 동일 라벨('기타','배당금' 등)이 여러 행에 존재하므로, 주간 템플릿에서 고정인
-- 행 번호(line_no)를 안정적 식별자로 사용한다. account 는 표시용 라벨(부모 > 자식).
create table if not exists public.cf_detail (
  snapshot_id  bigint not null references public.cf_snapshots(id) on delete cascade,
  line_no      int    not null,                 -- 2026_CF 행 번호 (안정적 식별자)
  account      text   not null,                 -- 표시 라벨 (예: '영업외지출 > 기타')
  fiscal_year  int    not null,
  month        int    not null check (month between 1 and 12),
  value        numeric,
  memo         text,                             -- 엑셀 셀 주석 (있을 때)
  primary key (snapshot_id, line_no, fiscal_year, month)
);

-- 자산매각·조달 파이프라인
create table if not exists public.cf_pipeline (
  snapshot_id  bigint not null references public.cf_snapshots(id) on delete cascade,
  seq          int    not null,
  item         text   not null,                 -- 예: 'TLT', '스테이지파이브'
  note         text,                             -- 예: '26년 매각 목표'
  primary key (snapshot_id, seq)
);

create index if not exists idx_cf_summary_lookup on public.cf_summary (account, fiscal_year, month);
create index if not exists idx_cf_detail_lookup  on public.cf_detail  (line_no, fiscal_year, month);

-- ----------------------------------------------------------------------------
-- 전주 대비 뷰: 각 스냅샷을 직전 스냅샷과 비교
-- ----------------------------------------------------------------------------

-- Summary 전주 대비 (KPI/차트 델타)
create or replace view public.cf_summary_wow as
select cur.snapshot_id, s.report_date,
       cur.section, cur.account, cur.fiscal_year, cur.month,
       cur.value                            as this_week,
       prev.value                           as last_week,
       cur.value - coalesce(prev.value, 0)  as delta
from public.cf_summary cur
join public.cf_snapshots s on s.id = cur.snapshot_id
left join lateral (
  select v.value
  from public.cf_summary v
  join public.cf_snapshots s2 on s2.id = v.snapshot_id
  where s2.report_date < s.report_date
    and v.account = cur.account
    and v.fiscal_year = cur.fiscal_year
    and v.month = cur.month
  order by s2.report_date desc
  limit 1
) prev on true;

-- 상세 라인아이템 변동 + 메모 (경영진 '변동 사유' 표)
-- 직전 스냅샷과 line_no 로 매칭(라벨 중복에 안전). 메모 있는 행이 '근본 사유'.
create or replace view public.cf_detail_changes as
select cur.snapshot_id, s.report_date,
       cur.line_no, cur.account, cur.fiscal_year, cur.month,
       prev.value                           as last_week,
       cur.value                            as this_week,
       cur.value - coalesce(prev.value, 0)  as delta,
       cur.memo
from public.cf_detail cur
join public.cf_snapshots s on s.id = cur.snapshot_id
left join lateral (
  select v.value
  from public.cf_detail v
  join public.cf_snapshots s2 on s2.id = v.snapshot_id
  where s2.report_date < s.report_date
    and v.line_no = cur.line_no
    and v.fiscal_year = cur.fiscal_year
    and v.month = cur.month
  order by s2.report_date desc
  limit 1
) prev on true
where abs(cur.value - coalesce(prev.value, 0)) >= 0.3;   -- 0.3억 이상만

-- ----------------------------------------------------------------------------
-- RLS: 익명 접근 차단. 대시보드는 인증 사용자 읽기, 적재는 service_role.
-- ----------------------------------------------------------------------------
alter table public.cf_snapshots enable row level security;
alter table public.cf_summary   enable row level security;
alter table public.cf_detail    enable row level security;
alter table public.cf_pipeline  enable row level security;

do $$
declare t text;
begin
  foreach t in array array['cf_snapshots','cf_summary','cf_detail','cf_pipeline'] loop
    execute format('drop policy if exists "auth read %1$s" on public.%1$s', t);
    execute format('create policy "auth read %1$s" on public.%1$s for select to authenticated using (true)', t);
  end loop;
end $$;
-- service_role 은 RLS 를 우회하므로 별도 write 정책 불필요.
