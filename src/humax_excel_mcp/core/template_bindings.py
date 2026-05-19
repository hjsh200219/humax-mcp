"""Per-sheet cell-range mappings for golden templates (PRD §4.9 / plan §2)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from . import errors

TemplateType = Literal["humax_allocation", "humax_account", "evcs_account"]


class RowSelection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    filter_column: str
    filter_values: list[str] = Field(default_factory=list)
    sort_by: list[str] = Field(default_factory=list)
    aggregate: bool = False


class SheetBinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sheet_name: str
    data_start_row: int = Field(ge=1)
    data_end_row: int = Field(ge=1)
    column_map: dict[str, str]
    row_key: list[str]
    row_selection: RowSelection
    skip_formula_rows: list[int] = Field(default_factory=list)


class TemplateBinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    template_type: TemplateType
    schema_version: str
    sheets: list[SheetBinding]

    def find_sheet(self, sheet_name: str) -> SheetBinding | None:
        for s in self.sheets:
            if s.sheet_name == sheet_name:
                return s
        return None


# --- Worked binding examples (1 per type — plan §5 US-016 AC4). ---

HUMAX_ALLOCATION_BINDING = TemplateBinding(
    template_type="humax_allocation",
    schema_version="2026.05",
    sheets=[
        SheetBinding(
            sheet_name="3월 누계",
            data_start_row=4,
            data_end_row=89,
            column_map={
                "B": "gl_account",
                "C": "gl_account_name",
                "D": "cum03_actual",
                "E": "cum02_actual",
            },
            row_key=["gl_account"],
            row_selection=RowSelection(
                filter_column="division",
                filter_values=["소조직"],
                sort_by=["gl_account"],
            ),
        ),
    ],
)

HUMAX_ACCOUNT_BINDING = TemplateBinding(
    template_type="humax_account",
    schema_version="2026.05",
    sheets=[
        SheetBinding(
            sheet_name="요약",
            data_start_row=5,
            data_end_row=73,
            column_map={
                "B": "gl_account",
                "C": "gl_account_name",
                "D": "annual_budget",
                "E": "annual_actual",
            },
            row_key=["gl_account"],
            row_selection=RowSelection(
                filter_column="company",
                filter_values=["HMX"],
                sort_by=["gl_account"],
            ),
        ),
    ],
)

EVCS_ACCOUNT_BINDING = TemplateBinding(
    template_type="evcs_account",
    schema_version="2026.05",
    sheets=[
        SheetBinding(
            sheet_name="요약",
            data_start_row=5,
            data_end_row=67,
            column_map={
                "B": "gl_account",
                "C": "gl_account_name",
                "D": "annual_actual",
            },
            row_key=["gl_account"],
            row_selection=RowSelection(
                filter_column="org_l1",
                filter_values=["EVCS국내", "EVCS해외"],
                sort_by=["gl_account"],
            ),
        ),
    ],
)


_REGISTRY: dict[str, TemplateBinding] = {
    "humax_allocation": HUMAX_ALLOCATION_BINDING,
    "humax_account": HUMAX_ACCOUNT_BINDING,
    "evcs_account": EVCS_ACCOUNT_BINDING,
}


def get_binding(template_type: str) -> TemplateBinding:
    if template_type not in _REGISTRY:
        raise errors.BindingNotFound(
            f"Unknown template_type: {template_type!r}. "
            f"Valid: {sorted(_REGISTRY.keys())}"
        )
    return _REGISTRY[template_type]
