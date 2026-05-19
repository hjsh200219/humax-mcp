"""Tool input pydantic v2 models."""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .bp26 import VALID_COMPANIES

CELL_PATTERN = re.compile(r"^[A-Z]{1,3}[1-9][0-9]*$")

RenderFormat = Literal["excel", "live_artifact", "both"]
OutputFormat = Literal["json", "csv", "markdown"]
SortBy = Literal["row_order", "variance_abs_desc", "amount_desc"]


class CellUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cell: str
    value: int | float | str
    skip_if_formula: bool = True

    @field_validator("cell")
    @classmethod
    def _cell_format(cls, v: str) -> str:
        if not CELL_PATTERN.match(v):
            raise ValueError(f"INVALID_CELL: {v}")
        return v


class AllocationUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cost_center: str
    allocation_basis: str
    new_rates: dict[str, float]


class ExtractRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    file_path: str
    sheet_name: str
    month: str | None = None
    company: str | None = None
    columns: list[str] | None = None
    org_level: str | None = None
    account_group: str | None = None
    max_rows: int = Field(default=500, ge=1, le=2000)
    sort_by: SortBy = "variance_abs_desc"
    output_format: OutputFormat = "json"
    render_format: RenderFormat = "excel"

    @field_validator("month")
    @classmethod
    def _month_fmt(cls, v: str | None) -> str | None:
        if v is None:
            return None
        if not re.match(r"^\d{4}-\d{2}$", v):
            raise ValueError(f"INVALID_MONTH_FORMAT: {v}")
        return v

    @field_validator("company")
    @classmethod
    def _company_valid(cls, v: str | None) -> str | None:
        if v is None or v in VALID_COMPANIES:
            return v
        raise ValueError(f"INVALID_COMPANY: {v}")


class VerifyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    file_path: str
    sheet_name: str
    levels: list[str] | None = None
    tolerance: float = Field(default=0.01, ge=0.0, le=1.0)
    check_formulas: bool = True
    render_format: RenderFormat = "excel"


class WriteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    file_path: str
    sheet_name: str
    updates: list[CellUpdate] = Field(min_length=1, max_length=5000)
    output_path: str | None = None
    dry_run: bool = False
    render_format: RenderFormat = "excel"


class DiffRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prev_file: str
    curr_file: str
    prev_sheet: str = "누계"
    curr_sheet: str = "누계"
    threshold_million: float = Field(default=10.0, ge=0.0)
    include_comment_draft: bool = True
    max_candidates: int = Field(default=100, ge=1, le=500)
    render_format: RenderFormat = "excel"


class AllocGetRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    file_path: str
    month: int = Field(ge=1, le=12)
    company: str | None = None
    cost_center: str | None = None
    render_format: RenderFormat = "excel"

    @field_validator("company")
    @classmethod
    def _company_valid(cls, v: str | None) -> str | None:
        if v is None or v in VALID_COMPANIES:
            return v
        raise ValueError(f"INVALID_COMPANY: {v}")


class AllocSetRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    file_path: str
    month: int = Field(ge=1, le=12)
    updates: list[AllocationUpdate] = Field(min_length=1)
    output_path: str
    dry_run: bool = False
    rate_tolerance: float = Field(default=0.01, ge=0.0)
    render_format: RenderFormat = "excel"


class ExchangeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    search_date: str | None = None
    target_currencies: list[str] | None = None
    fallback_to_previous: bool = True
    render_format: RenderFormat = "excel"

    @field_validator("search_date")
    @classmethod
    def _date_fmt(cls, v: str | None) -> str | None:
        if v is None:
            return None
        if not re.match(r"^\d{8}$", v):
            raise ValueError(f"INVALID_DATE_FORMAT: {v}")
        return v
