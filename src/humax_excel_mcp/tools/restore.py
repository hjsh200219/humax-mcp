"""restore_backup — PRD §4.11 / plan §5 US-018. Recovery tool with double-confirmation gate."""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path
from typing import Literal

from ..core import artifact_hints as ah
from ..core import backup as backup_mod
from ..core import errors, workbook_cache
from ..schemas.responses import RestoreBackupResult


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


async def restore_backup(
    backup_path: str,
    output_path: str,
    *,
    confirm_overwrite_original: bool = False,
    original_file_path: str | None = None,
    dry_run: bool = False,
    render_format: Literal["excel", "live_artifact", "both"] = "excel",
) -> RestoreBackupResult:
    """Restore a file from a previous backup. Side-file default; in-place requires double confirmation."""
    src = Path(backup_path)
    if not src.exists():
        raise errors.BackupNotFound(f"백업 파일을 찾을 수 없습니다: {src}")
    if src.suffix.lower() != ".xlsx":
        raise errors.BackupNotFound(f"백업은 xlsx여야 합니다: {src}")

    out = Path(output_path)

    is_in_place = (
        original_file_path is not None and out.resolve() == Path(original_file_path).resolve()
    )

    if is_in_place and not confirm_overwrite_original:
        raise errors.OverwriteOriginalForbidden(
            "output_path가 original_file_path와 동일합니다. "
            "in-place 복구는 confirm_overwrite_original=True가 필수입니다."
        )

    backup_sha = _sha256(src)

    pre_restore_backup_path: Path | None = None
    if dry_run:
        return RestoreBackupResult(
            dry_run=True,
            restored_path=None,
            backup_sha256=backup_sha,
            restored_sha256=None,
            pre_restore_backup_path=None,
            metadata={
                "backup_path": str(src),
                "output_path": str(out),
                "in_place": is_in_place,
                "would_create_pre_restore_backup": is_in_place,
            },
            render_format=render_format,
            artifact_hints=ah.maybe_hints(
                render_format,
                artifact_type="diff_cards",
                title="restore_backup dry-run preview",
            ),
        )

    if is_in_place and original_file_path is not None:
        orig = Path(original_file_path)
        if orig.exists():
            try:
                pre_restore_backup_path = backup_mod.create_backup(orig)
            except errors.BackupFailed:
                raise

    if not out.parent.exists():
        raise errors.WritePermissionDenied(f"출력 디렉터리가 없습니다: {out.parent}")

    try:
        shutil.copy2(src, out)
    except OSError as exc:
        raise errors.RestoreFailed(f"복구 실패: 복사 오류 — {exc}") from exc
    workbook_cache.invalidate(out)

    if not out.exists() or out.stat().st_size == 0:
        raise errors.RestoreFailed("복구 실패: 결과 파일 크기 0")

    restored_sha = _sha256(out)
    if restored_sha != backup_sha:
        raise errors.RestoreFailed(
            f"복구 실패: sha256 불일치 backup={backup_sha[:16]} restored={restored_sha[:16]}"
        )

    return RestoreBackupResult(
        dry_run=False,
        restored_path=str(out),
        backup_sha256=backup_sha,
        restored_sha256=restored_sha,
        pre_restore_backup_path=str(pre_restore_backup_path) if pre_restore_backup_path else None,
        metadata={
            "backup_path": str(src),
            "in_place": is_in_place,
            "original_file_path": original_file_path,
        },
        render_format=render_format,
        artifact_hints=ah.maybe_hints(
            render_format,
            artifact_type="diff_cards",
            title=f"restore_backup {'in-place' if is_in_place else 'side-file'}",
        ),
    )
