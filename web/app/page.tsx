import { getDashboard } from "@/lib/data";
import KpiBand from "@/components/KpiBand";
import EndingBalanceChart from "@/components/EndingBalanceChart";
import WaterfallChart from "@/components/WaterfallChart";
import WowTable from "@/components/WowTable";
import Pipeline from "@/components/Pipeline";

// 매 요청마다 최신 스냅샷을 조회 (주간 갱신 반영)
export const dynamic = "force-dynamic";

export default async function Page() {
  const d = await getDashboard();

  const minMonth = `${d.minLiquidity.month}월`;
  const minVal = d.minLiquidity.value;
  const shortName = (a: string) => (a.includes(">") ? a.split(">").pop()!.trim() : a);
  const cashColor = (cash: "pos" | "neg") => (cash === "pos" ? "var(--blue)" : "var(--neg)");

  return (
    <div className="wrap">
      <header>
        <div>
          <h1>휴맥스 Cash Forecast · 경영진 대시보드</h1>
          <div className="sub">
            기준일 <b>{d.reportDate}</b>
            {d.prevDate && <> · 전주({d.prevDate}) 대비</>} · 단위 억원
          </div>
        </div>
        <div className="tags">
          <span className="tag live">🟢 Supabase 연동</span>
          <span className="tag lock">🔒 비밀번호 보호</span>
        </div>
      </header>

      <div className="insight">
        📌 <b>이번 주 변동 요약</b> —{" "}
        {d.reasons.length ? (
          <>
            전주 대비 {d.reasons.length}개 항목 변동 —{" "}
            {d.reasons.map((g, i) => (
              <span key={g.account}>
                {i > 0 && " · "}
                <span style={{ color: cashColor(g.cash), fontWeight: 700 }}>
                  {shortName(g.account)} {g.cash === "pos" ? "▲" : "▼"} {Math.abs(g.net).toFixed(1)}억
                </span>
              </span>
            ))}
            . 연중 최저 유동성 {minMonth} {minVal.toFixed(1)}억.
          </>
        ) : (
          <>전주 대비 근본 변동 없음. 연중 최저 유동성 {minMonth} {minVal.toFixed(1)}억.</>
        )}
      </div>

      <KpiBand kpis={d.kpis} />

      <div className="row2">
        <div className="card">
          <h2>2026 월별 유동성 추이</h2>
          <div className="cs">유동성(가용현금) · 이번 주(실선) vs 전주(점선)</div>
          <EndingBalanceChart points={d.ending} />
        </div>
        <div className="card">
          <h2>2026 연간 현금흐름 (워터폴)</h2>
          <div className="cs">영업 → 투자 → 재무 → 종합수지</div>
          <WaterfallChart bars={d.waterfall} />
        </div>
      </div>

      <WowTable reasons={d.reasons} />
      <Pipeline items={d.pipeline} />

      <footer>
        휴맥스 주간 Cash Forecast · Supabase 스냅샷 자동 집계 · 경영진 보고용
      </footer>
    </div>
  );
}
