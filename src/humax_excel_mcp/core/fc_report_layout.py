"""FC 실적 보고서 ({월}(AC), {월} 누계(상세)) 시트의 고정 레이아웃 상수.

실데이터 기준 검증일: 2026-06-26 (4월->5월 업데이트). 원본 양식이 바뀌면 이 파일만 갱신.
"""

from __future__ import annotations

# ---- "{월}(AC)" 시트: BP(2-29)/실적(32-59)/Diff(62-89) 3블록, 블록 간 +30 오프셋 ----
# 대조직(raw col10, '대조직') -> 실적 블록 leaf row 번호
ALIAS_TO_ROW: dict[str, int] = {
    "사업 그룹": 37, "개발 그룹": 38, "SCM실": 39, "Media그룹": 40,
    "CEO": 42, "Staff(CEO)": 43, "경영지원실": 44, "HR실": 45,
    "HUS": 47, "HMX": 48, "HUK": 49, "HDG": 50, "HUG": 51, "HTR": 52,
    "HBR": 53, "HJP": 54, "HTH": 55, "HAU": 56, "HID": 57, "HSZ": 58,
}
LEAF_ROWS: list[int] = list(ALIAS_TO_ROW.values())

# AC 시트 세그먼트 열 -> raw "예산+실적" 시트 0-based 컬럼 인덱스
SEG_RAW_IDX: dict[str, int] = {
    "J": 45, "K": 46, "L": 47, "M": 48, "N": 49, "O": 50,
    "Q": 51, "R": 52, "S": 53, "T": 54, "U": 55, "V": 56, "W": 57,
}
# 주의: P열은 항상 '=SUM(Q:W)' 기존 수식이라 직접 쓰지 않음. F/G/H/I는 합계행 수식 영역.

RAW_COL_GUBUN = 0          # '예산'/'실적'
RAW_COL_MONTH = 2          # '1월'~'12월'
RAW_COL_HQCORP = 4         # 본사/법인 (라벨 중복 이슈 있어 누계(상세) 집계는 COL_COMPANY 사용)
RAW_COL_COMPANY = 5        # 본사/법인 판정용 신뢰 컬럼 (HKR=본사, 그 외=법인)
RAW_COL_ORG = 10           # '대조직' — ALIAS_TO_ROW 키
RAW_COL_DAEGYEJEONG_RE = 17
RAW_COL_AMOUNT_KRW = 23    # 권위있는 금액 필드 (col21 Amount(Doc)는 사용하지 않음)

# ---- "{월} 누계(상세)" 시트: 대계정 카테고리 x 본사/법인 x 사업부 ----
CAT_MAP: dict[str, str] = {
    "11 급여": "인건비", "53 4대보험료": "인건비", "13 퇴직급여": "인건비",
    "16 여비교통비": "여비교통비",
    "29 지급수수료": "지급수수료", "40 외주개발용역비": "지급수수료",
    "41 인증대행료": "지급수수료", "42 특허처리비": "지급수수료",
    "23 감가상각비": "감가상각비",
    "47 광고선전비": "광고선전비",
}  # 매핑 없는 대계정(re)는 전부 '기타'. 14 복리후생비/15 교육훈련비는 기타 (인건비 아님 — 검증 시 발견된 실수 주의)
CATS: list[str] = ["인건비", "여비교통비", "감가상각비", "지급수수료", "광고선전비", "기타"]
ROWS_HQ: dict[str, int] = {c: 5 + i for i, c in enumerate(CATS)}     # 본사: 행 5~10
ROWS_CORP: dict[str, int] = {c: 12 + i for i, c in enumerate(CATS)}  # 법인: 행 12~17
SEG_BLOCK_COLS: dict[str, tuple[str, str, str]] = {       # 사업부 -> (예산열, 실적열, 비고열)
    "총합계": ("C", "D", "G"), "STB": ("H", "I", "L"), "Mobility": ("M", "N", "Q"),
    "EVCS": ("R", "S", "V"), "공통": ("W", "X", "AA"), "건물": ("AB", "AC", "AF"),
    "Shared": ("AG", "AH", "AK"),
}
SEG_COLS_RAW: dict[str, int] = {  # 누계(상세) 집계용 — AC 시트와 다른 축(사업부 단위가 더 굵음)
    "STB": 45, "Mobility": 46, "EVCS_in": 47, "EVCS_out": 48, "공통": 49, "건물": 50, "Shared": 61,
}
COMMENT_THRESHOLD = 9_000_000   # 이 금액(원) 이상 차이 블록만 코멘트
COMMENT_ITEM_MIN = 5_000_000
COMMENT_TOPN = 3
