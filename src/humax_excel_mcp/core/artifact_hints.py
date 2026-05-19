"""Build ArtifactHints per PRD §4.5."""

from __future__ import annotations

from typing import Any

from ..schemas.responses import ArtifactHints


def build_hints(
    artifact_type: str,
    title: str,
    *,
    preferred_chart: str | None = None,
    columns_for_chart: list[str] | None = None,
    comparison_columns: list[str] | None = None,
    highlight_threshold: int | None = None,
    pii_redacted: bool = False,
    **extra: Any,
) -> ArtifactHints:
    payload: dict[str, Any] = {
        "type": artifact_type,
        "title": title,
        "preferred_chart": preferred_chart,
        "columns_for_chart": columns_for_chart,
        "comparison_columns": comparison_columns,
        "highlight_threshold": highlight_threshold,
        "pii_redacted": pii_redacted,
    }
    payload.update(extra)
    return ArtifactHints(**{k: v for k, v in payload.items() if v is not None or k == "pii_redacted"})


def maybe_hints(render_format: str, **kwargs: Any) -> ArtifactHints | None:
    if render_format in ("live_artifact", "both"):
        return build_hints(**kwargs)
    return None
