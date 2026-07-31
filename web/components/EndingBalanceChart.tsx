"use client";
import { useState } from "react";
import type { MonthlyPoint } from "@/lib/types";

const W = 760, H = 320, L = 52, R = 20, T = 20, B = 44;
const PW = W - L - R, PH = H - T - B;
const MONTHS = ["1월", "2월", "3월", "4월", "5월", "6월", "7월", "8월", "9월", "10월", "11월", "12월"];

export default function EndingBalanceChart({ points }: { points: MonthlyPoint[] }) {
  const [hover, setHover] = useState<number | null>(null);

  const vals = points.flatMap((p) => [p.thisWeek, p.lastWeek]).filter((v): v is number => v != null);
  const maxV = Math.max(1, ...vals);
  const ymax = Math.max(50, Math.ceil(maxV / 50) * 50);
  const step = ymax <= 150 ? 50 : 100;
  const grid: number[] = [];
  for (let g = 0; g <= ymax; g += step) grid.push(g);

  const X = (i: number) => L + i * (PW / (points.length - 1 || 1));
  const Y = (v: number) => T + PH - (v / ymax) * PH;

  const path = (key: "thisWeek" | "lastWeek") => {
    const seg = points
      .map((p, i) => (p[key] == null ? null : `${X(i).toFixed(1)} ${Y(p[key] as number).toFixed(1)}`))
      .filter(Boolean);
    return "M " + seg.join(" L ");
  };

  // 최저 thisWeek 지점
  let minIdx = -1, minVal = Infinity;
  points.forEach((p, i) => { if (p.thisWeek != null && p.thisWeek < minVal) { minVal = p.thisWeek; minIdx = i; } });

  const hp = hover != null ? points[hover] : null;

  return (
    <div className="chart-wrap">
      <svg viewBox={`0 0 ${W} ${H}`} className="chart" preserveAspectRatio="xMidYMid meet"
        role="img" aria-label="2026 월별 기말잔액 추이">
        {grid.map((g) => (
          <g key={g}>
            <line x1={L} y1={Y(g)} x2={W - R} y2={Y(g)} className="grid-l" />
            <text x={L - 8} y={Y(g) + 4} className="ytick">{g}</text>
          </g>
        ))}
        <path d={path("lastWeek")} className="line prev" />
        <path d={path("thisWeek")} className="line cur" />
        {points.map((p, i) =>
          p.thisWeek == null ? null : (
            <circle key={i} cx={X(i)} cy={Y(p.thisWeek)} r={i === minIdx ? 4.5 : 3.2}
              className={i === minIdx ? "dot dotmin" : "dot"} />
          )
        )}
        {minIdx >= 0 && (
          <g>
            <line x1={X(minIdx)} y1={Y(minVal)} x2={X(minIdx) - 70} y2={Y(minVal) - 46} className="conn" />
            <text x={X(minIdx) - 76} y={Y(minVal) - 52} className="xtick" style={{ textAnchor: "end", fontWeight: 700, fill: "var(--warn)" }}>
              유동성 최저 {MONTHS[points[minIdx].month - 1]} · {minVal.toFixed(1)}억
            </text>
          </g>
        )}
        {points.map((p, i) => (
          <text key={`x${i}`} x={X(i)} y={H - 16} className="xtick">{MONTHS[p.month - 1]}</text>
        ))}
        {/* hover hit targets */}
        {points.map((p, i) => (
          <circle key={`h${i}`} cx={X(i)} cy={p.thisWeek == null ? PH : Y(p.thisWeek)} r={16}
            className="hitdot" onMouseEnter={() => setHover(i)} onMouseLeave={() => setHover(null)} />
        ))}
      </svg>
      {hp && hp.thisWeek != null && (
        <div className="tip" style={{ left: `${(X(hover as number) / W) * 100}%`, top: `${(Y(hp.thisWeek) / H) * 100}%` }}>
          <b>{MONTHS[hp.month - 1]}</b> · 이번주 {hp.thisWeek.toFixed(1)}억
          {hp.lastWeek != null && <> · 전주 {hp.lastWeek.toFixed(1)}억 ({fmtDelta(hp.thisWeek - hp.lastWeek)})</>}
        </div>
      )}
      <div className="legend">
        <span><span className="sw" style={{ borderColor: "var(--blue)" }} />이번 주</span>
        <span><span className="sw" style={{ borderColor: "var(--gray)", borderTopStyle: "dashed" }} />전주</span>
        <span><span style={{ width: 10, height: 10, borderRadius: "50%", background: "var(--warn)" }} />유동성 최저</span>
      </div>
    </div>
  );
}

function fmtDelta(d: number) {
  const s = d > 0 ? "+" : "";
  return `${s}${d.toFixed(1)}`;
}
