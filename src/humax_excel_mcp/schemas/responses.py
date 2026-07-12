"""Tool output pydantic v2 models + ArtifactHints."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

ArtifactType = Literal[
    "table",
    "chart",
    "dashboard",
    "diff_cards",
    "verification_result",
    "table_with_chart",
    "before_after_bar",
    "rates_dashboard",
]

ChartType = Literal[
    "bar",
    "line",
    "pie",
    "tree",
    "stacked_bar",
    "before_after_bar",
]


class ArtifactHints(BaseModel):
    model_config = ConfigDict(extra="allow")

    type: ArtifactType
    title: str
    preferred_chart: ChartType | None = None
    columns_for_chart: list[str] | None = None
    comparison_columns: list[str] | None = None
    highlight_threshold: int | None = None
    pii_redacted: bool = False


class BaseResult(BaseModel):
    model_config = ConfigDict(extra="allow")

    status: Literal["ok", "error"] = "ok"
    success: bool = True
    data_classification: Literal["INTERNAL", "PUBLIC", "CONFIDENTIAL"] = "INTERNAL"
    render_format: Literal["excel", "live_artifact", "both"] = "excel"
    artifact_hints: ArtifactHints | None = None


class ExtractMetadata(BaseModel):
    model_config = ConfigDict(extra="allow")

    total_rows: int
    filtered_rows: int
    returned_rows: int
    truncated: bool
    filters_applied: dict[str, Any]
    sort_order: str
    estimated_tokens: int
    file_path: str
    sheet_name: str


class ExtractResult(BaseResult):
    data: list[dict[str, Any]] = Field(default_factory=list)
    metadata: ExtractMetadata


class LevelResult(BaseModel):
    model_config = ConfigDict(extra="allow")

    level: str
    expected: float
    actual: float
    difference: float
    status: Literal["PASS", "FAIL", "SKIPPED"]
    detail: str | None = None


class Anomaly(BaseModel):
    model_config = ConfigDict(extra="allow")

    row_index: int
    org: str
    account: str
    budget: float
    actual: float
    variance: float
    flag: str
    suggested_comment: str


class FormulaWarning(BaseModel):
    model_config = ConfigDict(extra="allow")

    cell: str
    expected_formula: str | None = None
    current_state: str
    warning: str


class VerifySummary(BaseModel):
    total_checks: int
    passed: int
    failed: int
    warnings: int
    skipped: int = 0


class VerifyResult(BaseResult):
    summary: VerifySummary
    level_results: list[LevelResult] = Field(default_factory=list)
    anomalies: list[Anomaly] = Field(default_factory=list)
    formula_warnings: list[FormulaWarning] = Field(default_factory=list)
    metadata: dict[str, Any]


class WriteSummary(BaseModel):
    total_updates: int
    applied: int
    skipped_formula: int
    skipped_invalid: int
    warnings: int


class WriteApplied(BaseModel):
    cell: str
    old_value: Any = None
    new_value: Any = None


class WriteSkipped(BaseModel):
    model_config = ConfigDict(extra="allow")

    cell: str
    reason: str
    formula: str | None = None


class WriteWarning(BaseModel):
    cell: str
    message: str


class WriteVerification(BaseModel):
    verified: bool
    mismatches: list[dict[str, Any]] = Field(default_factory=list)


class WriteResult(BaseResult):
    dry_run: bool
    summary: WriteSummary
    output_path: str | None = None
    backup_path: str | None = None
    applied: list[WriteApplied] = Field(default_factory=list)
    skipped: list[WriteSkipped] = Field(default_factory=list)
    warnings: list[WriteWarning] = Field(default_factory=list)
    verification: WriteVerification


class DiffSummary(BaseModel):
    total_cells_compared: int
    candidates_found: int
    candidates_returned: int
    truncated: bool
    largest_variance_million: float
    net_variance_million: float


class DiffCandidate(BaseModel):
    model_config = ConfigDict(extra="allow")

    row_index: int
    org: str
    sub_org: str | None = None
    account_code: str
    account_name: str
    prev_value: float
    curr_value: float
    diff: float
    diff_million: float
    diff_pct: float
    comment_draft: str | None = None
    severity: Literal["HIGH", "MEDIUM", "LOW"]


class DiffResult(BaseResult):
    summary: DiffSummary
    candidates: list[DiffCandidate] = Field(default_factory=list)
    structure_warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any]


class AllocationRateRow(BaseModel):
    model_config = ConfigDict(extra="allow")

    cost_center: str
    cost_center_name: str | None = None
    allocation_basis: str
    rates: dict[str, float]
    rate_sum: float
    rate_sum_ok: bool
    row_count: int


class AllocationRatesResult(BaseResult):
    data: list[AllocationRateRow] = Field(default_factory=list)
    metadata: dict[str, Any]


class AllocationChange(BaseModel):
    model_config = ConfigDict(extra="allow")

    cost_center: str
    before: dict[str, float]
    after: dict[str, float]
    rows_affected: int


class AllocationUpdateData(BaseModel):
    output_path: str | None = None
    backup_path: str | None = None
    updates_applied: int
    changes: list[AllocationChange] = Field(default_factory=list)


class AllocationUpdateResult(BaseResult):
    dry_run: bool
    data: AllocationUpdateData
    metadata: dict[str, Any]


class ExchangeRate(BaseModel):
    model_config = ConfigDict(extra="allow")

    cur_unit: str
    cur_nm: str | None = None
    deal_bas_r: float
    ttb: float | None = None
    tts: float | None = None
    kftc_deal_bas_r: float | None = None
    cur_unit_normalized: str | None = None
    unit_multiplier: int | None = None
    deal_bas_r_per_unit: float | None = None
    sanity_warning: bool = False


class ExchangeRatesData(BaseModel):
    search_date: str
    actual_date: str
    rates: list[ExchangeRate]


class ExchangeRatesResult(BaseResult):
    data: ExchangeRatesData
    metadata: dict[str, Any]


class TemplateBindingSummary(BaseModel):
    model_config = ConfigDict(extra="allow")

    sheet_name: str
    cells_to_populate: int
    formulas_preserved: int
    rows_matched: int = 0
    rows_unmatched: int = 0


class ApplyTemplateResult(BaseResult):
    dry_run: bool
    template_type: str
    output_path: str | None = None
    backup_path: str | None = None
    sheets_processed: list[TemplateBindingSummary] = Field(default_factory=list)
    verification: WriteVerification
    metadata: dict[str, Any]


class GenerateReportResult(BaseResult):
    dry_run: bool
    report_type: str
    output_path: str | None = None
    backup_path: str | None = None
    template_used: str | None = None
    verification: VerifySummary | None = None
    data_summary: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any]


class RestoreBackupResult(BaseResult):
    dry_run: bool
    restored_path: str | None = None
    backup_sha256: str
    restored_sha256: str | None = None
    pre_restore_backup_path: str | None = None
    metadata: dict[str, Any]


class FcMonthAcSummary(BaseModel):
    model_config = ConfigDict(extra="allow")

    sheet: str  # "{월}(AC)"
    formulas_restored: int
    cells_written: int
    unmatched_orgs: dict[str, float] = Field(default_factory=dict)
    raw_actual_total: float  # 해당월 raw "실적" Amount(KRW) 총합


class FcMonthCumulativeSummary(BaseModel):
    model_config = ConfigDict(extra="allow")

    ac_sheet_created: str  # "{월} 누계(AC)"
    detail_sheet_created: str  # "{월} 누계(상세)"
    prev_sheets_hidden: list[str] = Field(default_factory=list)
    formula_chain_extended: int  # build_ac_sheet에서 확장된 수식 셀 수


class FcMonthVerification(BaseModel):
    model_config = ConfigDict(extra="allow")

    verified: bool
    raw_direct_total: float
    derived_cumulative_total: float
    detail_grand_total: float
    diff: float
    tolerance: float


class FcMonthUpdateResult(BaseResult):
    dry_run: bool
    month: str
    prev_month: str
    output_path: str | None = None
    backup_path: str | None = None
    ac_summary: FcMonthAcSummary
    cumulative_summary: FcMonthCumulativeSummary
    verification: FcMonthVerification
    warnings: list[str] = Field(default_factory=list)
