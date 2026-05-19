"""US-018 restore_backup tests."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from humax_excel_mcp.core import errors
from humax_excel_mcp.tools.restore import restore_backup

pytestmark = pytest.mark.asyncio


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


async def test_happy_path_side_file(sample_26bp_path: Path, tmp_path: Path) -> None:
    out = tmp_path / "restored.xlsx"
    res = await restore_backup(
        backup_path=str(sample_26bp_path),
        output_path=str(out),
    )
    assert res.success
    assert out.exists()
    assert res.backup_sha256 == res.restored_sha256
    assert _sha(out) == _sha(sample_26bp_path)
    assert res.pre_restore_backup_path is None


async def test_in_place_requires_confirm(
    sample_26bp_path: Path, tmp_path: Path
) -> None:
    target = tmp_path / "original.xlsx"
    target.write_bytes(sample_26bp_path.read_bytes())
    backup = tmp_path / "backup.xlsx"
    backup.write_bytes(sample_26bp_path.read_bytes())
    with pytest.raises(errors.OverwriteOriginalForbidden):
        await restore_backup(
            backup_path=str(backup),
            output_path=str(target),
            confirm_overwrite_original=False,
            original_file_path=str(target),
        )


async def test_in_place_with_confirm_creates_pre_restore_backup(
    sample_26bp_path: Path, tmp_path: Path
) -> None:
    target = tmp_path / "original.xlsx"
    target.write_bytes(sample_26bp_path.read_bytes())
    backup = tmp_path / "backup.xlsx"
    backup.write_bytes(sample_26bp_path.read_bytes())
    res = await restore_backup(
        backup_path=str(backup),
        output_path=str(target),
        confirm_overwrite_original=True,
        original_file_path=str(target),
    )
    assert res.success
    assert res.pre_restore_backup_path
    assert Path(res.pre_restore_backup_path).exists()


async def test_backup_not_found(tmp_path: Path) -> None:
    with pytest.raises(errors.BackupNotFound):
        await restore_backup(
            backup_path=str(tmp_path / "missing.xlsx"),
            output_path=str(tmp_path / "out.xlsx"),
        )


async def test_dry_run_no_write(sample_26bp_path: Path, tmp_path: Path) -> None:
    out = tmp_path / "out.xlsx"
    res = await restore_backup(
        backup_path=str(sample_26bp_path),
        output_path=str(out),
        dry_run=True,
    )
    assert res.dry_run is True
    assert res.restored_path is None
    assert res.restored_sha256 is None
    assert not out.exists()
    assert res.backup_sha256 == _sha(sample_26bp_path)
