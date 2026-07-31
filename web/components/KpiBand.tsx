import type { Kpi } from "@/lib/types";

export default function KpiBand({ kpis }: { kpis: Kpi[] }) {
  return (
    <div className="kgrid">
      {kpis.map((k) => (
        <div key={k.label} className={`kpi ${k.tone}`}>
          <div className="klabel">{k.label}</div>
          <div className="kval">
            {fmt(k.value)}
            <span className="kunit">{k.unit}</span>
          </div>
          <div className="kfoot">
            {k.delta == null || Math.abs(k.delta) < 0.005 ? (
              <span className="badge flat">변동 없음</span>
            ) : (
              <span className={`badge ${k.delta > 0 ? "up" : "down"}`}>
                {k.delta > 0 ? "▲" : "▼"} {k.delta > 0 ? "+" : ""}{k.delta.toFixed(2)}
              </span>
            )}
            <span className="ksub">{k.sub}</span>
          </div>
        </div>
      ))}
    </div>
  );
}

function fmt(v: number) {
  return Number.isInteger(v) ? v.toString() : v.toFixed(1);
}
