import type { PipelineItem } from "@/lib/types";

export default function Pipeline({ items }: { items: PipelineItem[] }) {
  return (
    <div className="card fullw">
      <h2>자산매각 · 조달 파이프라인</h2>
      <div className="cs">유동성 확보 진행 현황</div>
      <div className="pgrid">
        {items.map((p) => (
          <div key={p.seq} className="pcard">
            <div className="pname">{p.item}</div>
            {p.note && <div className="pnote">{p.note}</div>}
          </div>
        ))}
      </div>
    </div>
  );
}
