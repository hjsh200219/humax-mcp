"use client";
import { useState } from "react";
import type { WaterfallBar } from "@/lib/types";

const W = 760, H = 300, L = 52, R = 20, T = 20, B = 44;
const PW = W - L - R, PH = H - T - B;

export default function WaterfallChart({ bars }: { bars: WaterfallBar[] }) {
  const [hover, setHover] = useState<number | null>(null);

  // 누적으로 도달하는 최소/최대 결정
  let cum = 0;
  const reach: number[] = [0];
  bars.forEach((b) => { if (b.kind !== "net") { cum += b.value; } reach.push(cum); reach.push(b.kind === "net" ? b.value : cum); });
  const lo = Math.min(0, ...reach), hi = Math.max(0, ...reach);
  const pad = Math.max(20, (hi - lo) * 0.12);
  const ymin = Math.floor((lo - pad) / 50) * 50;
  const ymax = Math.ceil((hi + pad) / 50) * 50;
  const Y = (v: number) => T + PH - ((v - ymin) / (ymax - ymin)) * PH;

  const bw = 64;
  const gap = (PW - bw * bars.length) / (bars.length - 1);
  const xOf = (i: number) => L + i * (bw + gap);

  const grid: number[] = [];
  for (let g = ymin; g <= ymax; g += 100) grid.push(g);

  // 막대 좌표 계산
  cum = 0;
  const rects = bars.map((b, i) => {
    let y: number, h: number;
    if (b.kind === "net") { y = Y(Math.max(0, b.value)); h = Math.abs(Y(b.value) - Y(0)); }
    else { const start = cum, end = cum + b.value; y = Y(Math.max(start, end)); h = Math.abs(Y(end) - Y(start)); cum = end; }
    return { ...b, i, x: xOf(i), y, h };
  });
  // 연결선
  cum = 0;
  const conns = bars.slice(0, -1).map((b, i) => { const end = cum + b.value; const ey = Y(end); cum = end; return { x1: xOf(i) + bw, x2: xOf(i + 1), y: ey }; });

  const hb = hover != null ? rects[hover] : null;

  return (
    <div className="chart-wrap">
      <svg viewBox={`0 0 ${W} ${H}`} className="chart" preserveAspectRatio="xMidYMid meet"
        role="img" aria-label="2026 연간 현금흐름 워터폴">
        {grid.map((g) => (
          <g key={g}>
            <line x1={L} y1={Y(g)} x2={W - R} y2={Y(g)} className="grid-l" />
            <text x={L - 8} y={Y(g) + 4} className="ytick">{g}</text>
          </g>
        ))}
        <line x1={L} y1={Y(0)} x2={W - R} y2={Y(0)} className="zero" />
        {conns.map((c, i) => <line key={i} x1={c.x1} y1={c.y} x2={c.x2} y2={c.y} className="conn" />)}
        {rects.map((r) => (
          <g key={r.i} onMouseEnter={() => setHover(r.i)} onMouseLeave={() => setHover(null)} style={{ cursor: "pointer" }}>
            <rect x={r.x} y={r.y} width={bw} height={r.h} rx={4} className={`wb ${r.kind}`} />
            <text x={r.x + bw / 2} y={H - 24} className="xtick">{r.name}</text>
            <text x={r.x + bw / 2} y={r.value >= 0 ? r.y - 6 : r.y + r.h + 14} className={`wval ${r.kind}`}>
              {r.value > 0 ? "+" : ""}{Math.round(r.value)}
            </text>
          </g>
        ))}
      </svg>
      {hb && (
        <div className="tip" style={{ left: `${((hb.x + bw / 2) / W) * 100}%`, top: `${(hb.y / H) * 100}%` }}>
          <b>{hb.name}</b> · {hb.value > 0 ? "+" : ""}{hb.value.toFixed(1)}억
        </div>
      )}
    </div>
  );
}
