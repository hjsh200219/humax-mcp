"""휴맥스 Cash Forecast 주간 엑셀 → 정규화 스냅샷 (→ Supabase 적재).

주차별 Cash Forecast 엑셀을 읽어 대시보드용 long-format 레코드로 변환한다.

추출 대상:
- Summary(MMDD) 시트 → KPI/차트 값 (cf_summary): 2024/2025/2026 월별
- '1. 2026_CF' 시트 → 상세 라인아이템 + 셀 메모 (cf_detail): 2026 월별 + 주석
- Summary 하단 파이프라인 → 자산매각·조달 현황 (cf_pipeline)

전주 대비 변동/변동 사유는 DB 뷰(cf_summary_wow, cf_detail_changes)가
직전 스냅샷과 비교해 계산하므로, 여기서는 '이번 주 스냅샷'만 만든다.

원본 숫자는 GitHub 에 저장하지 않는다(레포 public). --out 산출물과 엑셀은
.gitignore 로 차단되어 있으며, 실제 값은 Supabase(비공개)에만 적재한다.

Usage:
    # 1) dry-run: 파싱 결과를 JSON 으로 출력(적재 안 함)
    python scripts/ingest_cashflow.py "휴맥스Cash forecast (20260731).xlsx" --out snapshot.json

    # 2) 적재: 환경변수 SUPABASE_URL, SUPABASE_SERVICE_KEY 필요
    python scripts/ingest_cashflow.py "...(20260731).xlsx" --push
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

import openpyxl

# --- 열 배치 (Summary & 2026_CF 공통) --------------------------------------
# 2024 = C..N(3..14), 2025 = O..Z(15..26), 2026 = AA..AL(27..38)
YEAR_COLS = {
    2024: list(range(3, 15)),
    2025: list(range(15, 27)),
    2026: list(range(27, 39)),
}
WOW_THRESHOLD = 0.3  # 억원

# --- Summary 시트 행 매핑 (section, account) --------------------------------
SUMMARY_ROWS: dict[int, tuple[str, str]] = {
    4:  ("beginning", "기초잔액"),
    5:  ("operating", "영업활동 증감"),
    6:  ("operating", "영업수입"),
    12: ("operating", "영업외수입"),
    16: ("operating", "영업지출"),
    23: ("operating", "영업외지출"),
    29: ("investing", "투자활동 증감"),
    30: ("investing", "투자수입"),
    31: ("investing", "투자지출"),
    33: ("financing", "재무활동 증감"),
    34: ("financing", "조달"),
    40: ("financing", "상환"),
    46: ("net",       "종합수지"),
    47: ("ending",    "기말잔액"),
    48: ("ending",    "유동성"),
    49: ("ending",    "비유동성"),
    50: ("debt",      "차입금"),
    51: ("netcash",   "Net cash"),
}
PIPELINE_ROWS = range(102, 119)  # Summary 하단 자산매각/조달 파이프라인
PIPELINE_ITEM_COL = 1            # A
PIPELINE_NOTE_COL = 39           # AM


def _num(v) -> float | None:
    return float(v) if isinstance(v, (int, float)) else None


def report_date_from_name(path: Path) -> str:
    """파일명의 8자리(YYYYMMDD) → ISO 날짜."""
    m = re.search(r"(20\d{2})(\d{2})(\d{2})", path.name)
    if not m:
        raise ValueError(f"파일명에서 날짜(YYYYMMDD)를 찾지 못함: {path.name}")
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"


def _summary_sheet_name(names: list[str]) -> str:
    for n in names:
        if n.startswith("Summary(") and re.search(r"\d", n) and "2023" not in n:
            return n
    raise ValueError("Summary(MMDD) 시트를 찾지 못함")


def parse(path: Path) -> dict:
    wb_v = openpyxl.load_workbook(path, data_only=True)   # 값
    wb_c = openpyxl.load_workbook(path)                     # 주석(메모)

    summary_name = _summary_sheet_name(wb_v.sheetnames)
    ws = wb_v[summary_name]

    summary: list[dict] = []
    for row, (section, account) in SUMMARY_ROWS.items():
        for fy, cols in YEAR_COLS.items():
            for m, col in enumerate(cols, start=1):
                val = _num(ws.cell(row, col).value)
                if val is None:
                    continue
                summary.append({
                    "section": section, "account": account,
                    "fiscal_year": fy, "month": m, "value": round(val, 4),
                })

    # 2026_CF 상세 + 메모 (2026 열만)
    # 동일 라벨('기타','배당금' 등)이 여러 행에 존재 → 행 번호(line_no)로 식별하고,
    # 들여쓰기로 부모 라벨을 추적해 표시용 라벨을 '부모 > 자식'으로 명확화한다.
    detail: list[dict] = []
    if "1. 2026_CF" in wb_v.sheetnames:
        dv = wb_v["1. 2026_CF"]
        dc = wb_c["1. 2026_CF"]
        parent = ""
        for r in range(4, 57):
            raw = dv.cell(r, 1).value
            if raw is None or not str(raw).strip():
                continue
            label = str(raw).strip()
            indent = len(str(raw)) - len(str(raw).lstrip())
            if indent == 0:
                parent = label
                account = label
            else:
                account = f"{parent} > {label}" if parent else label
            for m, col in enumerate(YEAR_COLS[2026], start=1):
                val = _num(dv.cell(r, col).value)
                com = dc.cell(r, col).comment
                memo = None
                if com and com.text and com.text.strip():
                    memo = com.text.strip().replace("이유림:", "").replace("\n", " ").strip()
                if val is None and memo is None:
                    continue
                detail.append({
                    "line_no": r, "account": account, "fiscal_year": 2026, "month": m,
                    "value": round(val, 4) if val is not None else None, "memo": memo,
                })

    # 파이프라인
    pipeline: list[dict] = []
    for seq, r in enumerate(PIPELINE_ROWS, start=1):
        item = ws.cell(r, PIPELINE_ITEM_COL).value
        if not item or not str(item).strip():
            continue
        note = ws.cell(r, PIPELINE_NOTE_COL).value
        pipeline.append({
            "seq": seq, "item": str(item).strip(),
            "note": str(note).strip() if note else None,
        })

    return {
        "report_date": report_date_from_name(path),
        "source_file": path.name,
        "summary_sheet": summary_name,
        "counts": {"summary": len(summary), "detail": len(detail), "pipeline": len(pipeline)},
        "summary": summary,
        "detail": detail,
        "pipeline": pipeline,
    }


def push(snap: dict) -> None:
    """Supabase(PostgREST)로 upsert. SUPABASE_URL / SUPABASE_SERVICE_KEY 필요."""
    import httpx

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY")
    if not url or not key:
        sys.exit("환경변수 SUPABASE_URL / SUPABASE_SERVICE_KEY 가 필요합니다.")
    base = url.rstrip("/") + "/rest/v1"
    h = {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}

    with httpx.Client(timeout=30) as c:
        # 1) 스냅샷 upsert (report_date 기준) → id 회수
        r = c.post(f"{base}/cf_snapshots",
                   params={"on_conflict": "report_date"},
                   headers={**h, "Prefer": "resolution=merge-duplicates,return=representation"},
                   json={"report_date": snap["report_date"], "source_file": snap["source_file"]})
        r.raise_for_status()
        sid = r.json()[0]["id"]

        # 2) 기존 자식 레코드 삭제 후 재적재(멱등)
        for tbl in ("cf_summary", "cf_detail", "cf_pipeline"):
            c.delete(f"{base}/{tbl}", params={"snapshot_id": f"eq.{sid}"}, headers=h).raise_for_status()

        def bulk(tbl: str, rows: list[dict]) -> None:
            for i in range(0, len(rows), 500):
                chunk = [{**row, "snapshot_id": sid} for row in rows[i:i + 500]]
                c.post(f"{base}/{tbl}", headers=h, json=chunk).raise_for_status()

        bulk("cf_summary", snap["summary"])
        bulk("cf_detail", snap["detail"])
        bulk("cf_pipeline", snap["pipeline"])
    print(f"✅ 적재 완료: snapshot_id={sid} ({snap['report_date']}) "
          f"summary={len(snap['summary'])} detail={len(snap['detail'])} pipeline={len(snap['pipeline'])}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="휴맥스 Cash Forecast 엑셀 → 스냅샷/적재")
    ap.add_argument("xlsx", type=Path, help="Cash forecast 엑셀 경로")
    ap.add_argument("--out", type=Path, help="파싱 결과 JSON 저장 경로 (dry-run)")
    ap.add_argument("--push", action="store_true", help="Supabase 에 적재")
    args = ap.parse_args(argv)

    if not args.xlsx.exists():
        return int(bool(sys.stderr.write(f"파일 없음: {args.xlsx}\n")) or 2)

    snap = parse(args.xlsx)
    print(f"[{snap['report_date']}] {snap['summary_sheet']} · "
          f"summary={snap['counts']['summary']} detail={snap['counts']['detail']} "
          f"pipeline={snap['counts']['pipeline']}")

    if args.out:
        args.out.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"📄 저장: {args.out}")
    if args.push:
        push(snap)
    if not args.out and not args.push:
        json.dump(snap, sys.stdout, ensure_ascii=False, indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
