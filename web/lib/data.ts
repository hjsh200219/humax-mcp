import "server-only";
import { supabase } from "./supabase";
import type { Dashboard, Kpi, MonthlyPoint, PipelineItem, ReasonGroup, ReasonRow, WaterfallBar } from "./types";

const YEAR = 2026;

/** 대시보드에 필요한 모든 데이터를 최신 스냅샷 기준으로 조회한다. */
export async function getDashboard(): Promise<Dashboard> {
  // 1) 최신 스냅샷 (+ 직전 스냅샷 날짜)
  const { data: snaps, error: se } = await supabase
    .from("cf_snapshots")
    .select("id, report_date")
    .order("report_date", { ascending: false })
    .limit(2);
  if (se) throw se;
  if (!snaps || snaps.length === 0) throw new Error("적재된 스냅샷이 없습니다. scripts/ingest_cashflow.py --push 실행 필요.");
  const latest = snaps[0];
  const reportDate: string = latest.report_date;
  const prevDate: string | null = snaps[1]?.report_date ?? null;

  // 2) 2026 월별 유동성 (Summary 48행) — 대시보드 기본 현금 지표.
  //    기말잔액(47행)이 아니라 실제 가용 현금인 유동성(= 기말잔액 − 비유동성).
  const liqRows = await wowFor(reportDate, ["유동성"]);
  const ending: MonthlyPoint[] = [...liqRows]
    .sort((a, b) => a.month - b.month)
    .map((r) => ({ month: r.month, thisWeek: num(r.this_week), lastWeek: num(r.last_week) }));

  // 3) KPI 값
  const liqDec = liqRows.find((r) => r.month === 12);
  // 최저 유동성(요약 문구용) — KPI 밴드에는 노출하지 않음
  let minLiqThis = Infinity, minLiqMonth = 0;
  for (const r of liqRows) {
    const tv = num(r.this_week);
    if (tv != null && tv < minLiqThis) { minLiqThis = tv; minLiqMonth = r.month; }
  }
  const minLiqVal = Number.isFinite(minLiqThis) ? round(minLiqThis) : 0;

  const debtRows = await wowFor(reportDate, ["차입금"]);
  const debtDec = debtRows.find((r) => r.month === 12);

  // 연간 현금흐름 (2026 합계) — 이번주/직전주 대조로 델타 산출
  const flowAccounts = ["영업활동 증감", "투자활동 증감", "재무활동 증감"];
  const wf = await annualSums(latest.id, flowAccounts);
  const wfPrev = prevDate ? await annualSums(snaps[1].id, flowAccounts) : {};
  const flowKpi = (label: string, acct: string): Kpi => {
    const cur = round(wf[acct] ?? 0);
    const prev = wfPrev[acct];
    const d = prevDate ? round(cur - (prev ?? 0)) : null;
    const sub = !prevDate ? "-" : d != null && Math.abs(d) < 0.005 ? "전주와 동일" : `전주 ${(prev ?? 0).toFixed(1)}억`;
    return kpi(label, cur, "억", d, cur >= 0 ? "good" : "bad", sub);
  };

  const kpis: Kpi[] = [
    kpi("연말 유동성", val(liqDec?.this_week), "억", delta(liqDec), "warn",
      prevDate ? `전주 ${fmt(liqDec?.last_week)}억` : "전주 데이터 없음"),
    kpi("연말 차입금", val(debtDec?.this_week), "억", delta(debtDec), "neutral",
      deltaZero(debtDec) ? "전주와 동일" : (prevDate ? `전주 ${fmt(debtDec?.last_week)}억` : "-")),
    flowKpi("연간 영업현금흐름", "영업활동 증감"),
    flowKpi("연간 투자현금흐름", "투자활동 증감"),
    flowKpi("연간 재무현금흐름", "재무활동 증감"),
  ];

  // 4) 워터폴 (2026 연간 합계) — 영업/투자/재무 → 종합수지
  const waterfall: WaterfallBar[] = [
    { name: "영업활동", value: wf["영업활동 증감"] ?? 0, kind: bar(wf["영업활동 증감"]) },
    { name: "투자활동", value: wf["투자활동 증감"] ?? 0, kind: bar(wf["투자활동 증감"]) },
    { name: "재무활동", value: wf["재무활동 증감"] ?? 0, kind: bar(wf["재무활동 증감"]) },
    { name: "종합수지", value: (wf["영업활동 증감"] ?? 0) + (wf["투자활동 증감"] ?? 0) + (wf["재무활동 증감"] ?? 0), kind: "net" },
  ];

  // 5) 전주 대비 변동 사유 — 근본 계정(메모 있는 라인)을 찾아,
  //    해당 계정의 '모든 월'을 직전 스냅샷과 대조해 순증(net)이 정확히 맞도록 그룹화.
  const reasons = await buildReasonGroups(latest.id, snaps[1]?.id ?? null, reportDate);

  // 6) 파이프라인
  const { data: pipeRows, error: pe } = await supabase
    .from("cf_pipeline")
    .select("seq, item, note")
    .eq("snapshot_id", latest.id)
    .order("seq", { ascending: true });
  if (pe) throw pe;
  const pipeline: PipelineItem[] = (pipeRows ?? []).map((r) => ({ seq: r.seq, item: r.item, note: r.note }));

  return {
    reportDate, prevDate, ending, kpis, waterfall, reasons, pipeline,
    minLiquidity: { month: minLiqMonth, value: minLiqVal },
  };
}

// --- reason grouping -------------------------------------------------------

/**
 * 근본 변동 계정을 그룹으로 묶어 순증(net)을 정확히 계산한다.
 * 1) 메모가 달린 변동이 있는 라인(line_no)을 근본 계정으로 식별
 * 2) 그 라인들의 12개월 값을 이번주/직전주 스냅샷에서 모두 가져와 대조
 * 3) 월별 델타(|Δ|≥0.3만 표시)와 전체 순증(모든 월 합, 정확)을 산출
 */
async function buildReasonGroups(latestId: number, prevId: number | null, reportDate: string): Promise<ReasonGroup[]> {
  if (prevId == null) return [];

  // 1) 메모 달린 변동이 있는 근본 라인
  const { data: memoRows, error: me } = await supabase
    .from("cf_detail_changes")
    .select("line_no")
    .eq("report_date", reportDate)
    .not("memo", "is", null);
  if (me) throw me;
  const lineNos = [...new Set((memoRows ?? []).map((r) => r.line_no as number))];
  if (lineNos.length === 0) return [];

  // 2) 해당 라인들의 전 월 값 (이번주/직전주)
  const [curRes, prevRes] = await Promise.all([
    supabase.from("cf_detail").select("line_no, account, month, value, memo").eq("snapshot_id", latestId).in("line_no", lineNos),
    supabase.from("cf_detail").select("line_no, month, value").eq("snapshot_id", prevId).in("line_no", lineNos),
  ]);
  if (curRes.error) throw curRes.error;
  if (prevRes.error) throw prevRes.error;

  const key = (l: number, m: number) => `${l}:${m}`;
  const curVal = new Map<string, number | null>();
  const curMemo = new Map<string, string | null>();
  const accountOf = new Map<number, string>();
  for (const r of curRes.data ?? []) {
    curVal.set(key(r.line_no, r.month), num(r.value));
    if (r.memo) curMemo.set(key(r.line_no, r.month), r.memo as string);
    accountOf.set(r.line_no, r.account);
  }
  const prevVal = new Map<string, number | null>();
  for (const r of prevRes.data ?? []) prevVal.set(key(r.line_no, r.month), num(r.value));

  const groups: ReasonGroup[] = [];
  for (const line of lineNos) {
    let net = 0;
    const rows: ReasonRow[] = [];
    for (let m = 1; m <= 12; m++) {
      const cv = curVal.get(key(line, m)) ?? null;
      const pv = prevVal.get(key(line, m)) ?? null;
      const d = (cv ?? 0) - (pv ?? 0);
      net += d;
      if (Math.abs(d) >= 0.3) {
        rows.push({
          month: m,
          lastWeek: pv,
          thisWeek: cv,
          delta: round(d),
          memo: curMemo.get(key(line, m)) ?? null,
          cash: cashDir(accountOf.get(line) ?? "", d),
        });
      }
    }
    if (rows.length === 0) continue;
    net = round(net);
    groups.push({ account: accountOf.get(line) ?? String(line), net, cash: cashDir(accountOf.get(line) ?? "", net), rows });
  }
  // 순증 절대값 큰 순
  return groups.sort((a, b) => Math.abs(b.net) - Math.abs(a.net));
}

/** 수입 계정은 +가 현금 유입, 지출 계정은 +가 현금 유출. */
function cashDir(account: string, d: number): "pos" | "neg" {
  const isIncome = account.includes("수입") || account.includes("환급") || account.includes("배당");
  const positiveCash = isIncome ? d > 0 : d < 0;
  return positiveCash ? "pos" : "neg";
}

// --- helpers ---------------------------------------------------------------

type WowRow = { account: string; month: number; this_week: number | null; last_week: number | null };

async function wowFor(reportDate: string, accounts: string[]): Promise<WowRow[]> {
  const { data, error } = await supabase
    .from("cf_summary_wow")
    .select("account, month, this_week, last_week")
    .eq("report_date", reportDate)
    .eq("fiscal_year", YEAR)
    .in("account", accounts);
  if (error) throw error;
  return (data ?? []) as WowRow[];
}

async function annualSums(snapshotId: number, accounts: string[]): Promise<Record<string, number>> {
  const { data, error } = await supabase
    .from("cf_summary")
    .select("account, value")
    .eq("snapshot_id", snapshotId)
    .eq("fiscal_year", YEAR)
    .in("account", accounts);
  if (error) throw error;
  const out: Record<string, number> = {};
  for (const r of data ?? []) out[r.account] = (out[r.account] ?? 0) + (num(r.value) ?? 0);
  for (const k of Object.keys(out)) out[k] = round(out[k]);
  return out;
}

function num(v: unknown): number | null {
  if (v == null) return null;
  const n = typeof v === "number" ? v : Number(v);
  return Number.isFinite(n) ? n : null;
}
function round(n: number): number {
  return Math.round(n * 100) / 100;
}
function val(v: unknown): number {
  return round(num(v) ?? 0);
}
function fmt(v: unknown): string {
  return round(num(v) ?? 0).toFixed(1);
}
function delta(r?: WowRow): number | null {
  if (!r) return null;
  const d = (num(r.this_week) ?? 0) - (num(r.last_week) ?? 0);
  return round(d);
}
function deltaZero(r?: WowRow): boolean {
  const d = delta(r);
  return d != null && Math.abs(d) < 0.005;
}
function bar(v: number | undefined): "pos" | "neg" {
  return (v ?? 0) >= 0 ? "pos" : "neg";
}
function kpi(label: string, value: number, unit: string, d: number | null, tone: Kpi["tone"], sub: string): Kpi {
  return { label, value: round(value), unit, delta: d == null ? null : round(d), tone, sub };
}
