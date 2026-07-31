import { Fragment } from "react";
import type { ReasonGroup } from "@/lib/types";

export default function WowTable({ reasons }: { reasons: ReasonGroup[] }) {
  return (
    <div className="card fullw">
      <h2>전주 대비 변동 상세</h2>
      <div className="cs">
        동일 계정은 전 월을 합산해 <b>현금 순영향</b>을 표기 ·{" "}
        <span style={{ color: "var(--blue)", fontWeight: 700 }}>▲ 유입</span> /{" "}
        <span style={{ color: "var(--neg)", fontWeight: 700 }}>▼ 유출</span>
      </div>
      {reasons.length === 0 ? (
        <div className="wnote">전주 대비 근본 변동 항목이 없습니다.</div>
      ) : (
        <table>
          <thead>
            <tr>
              <th>항목</th>
              <th>월</th>
              <th className="num">전주</th>
              <th className="num">이번주</th>
              <th className="num">현금영향</th>
              <th>변동 사유</th>
            </tr>
          </thead>
          <tbody>
            {reasons.map((g) => (
              <Fragment key={g.account}>
                <tr className="grouprow">
                  <td colSpan={6}>
                    <b>{g.account}</b>{" "}
                    <span className={`netbadge ${g.cash === "pos" ? "cashin" : "cashout"}`}>
                      {g.cash === "pos" ? "▲" : "▼"} {Math.abs(g.net).toFixed(1)}억
                    </span>
                  </td>
                </tr>
                {g.rows.map((r) => (
                  <tr key={r.month}>
                    <td />
                    <td>{r.month}월</td>
                    <td className="num">{r.lastWeek == null ? "—" : r.lastWeek.toFixed(1)}</td>
                    <td className="num">{r.thisWeek == null ? "—" : r.thisWeek.toFixed(1)}</td>
                    <td className={`num ${r.cash === "pos" ? "cashin" : "cashout"}`}>
                      {r.cash === "pos" ? "▲" : "▼"} {Math.abs(r.delta).toFixed(1)}
                    </td>
                    <td className="reason">{r.memo ?? ""}</td>
                  </tr>
                ))}
              </Fragment>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
