export type Tone = "warn" | "bad" | "neutral" | "good";

export type MonthlyPoint = {
  month: number;
  thisWeek: number | null;
  lastWeek: number | null;
};

export type Kpi = {
  label: string;
  value: number;
  unit: string;
  delta: number | null; // null = 변동 없음/해당없음
  tone: Tone;
  sub: string;
};

export type WaterfallBar = {
  name: string;
  value: number;
  kind: "pos" | "neg" | "net";
};

export type ReasonRow = {
  month: number;
  lastWeek: number | null;
  thisWeek: number | null;
  delta: number;
  memo: string | null;
  cash: "pos" | "neg"; // 현금 영향
};

// 같은 계정(라인)의 모든 월을 합산해 전주 대비 순증(net)이 정확히 맞도록 그룹화
export type ReasonGroup = {
  account: string;
  net: number;
  cash: "pos" | "neg";
  rows: ReasonRow[];
};

export type PipelineItem = {
  seq: number;
  item: string;
  note: string | null;
};

export type Dashboard = {
  reportDate: string;
  prevDate: string | null;
  ending: MonthlyPoint[]; // 2026 월별 유동성
  minLiquidity: { month: number; value: number }; // 연중 최저 유동성 (요약 문구용)
  kpis: Kpi[];
  waterfall: WaterfallBar[];
  reasons: ReasonGroup[];
  pipeline: PipelineItem[];
};
