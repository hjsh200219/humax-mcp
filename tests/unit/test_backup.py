"""US-004 backup tests."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from humax_excel_mcp.core import backup, errors


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def test_create_backup_basic(sample_26bp_path: Path) -> None:
    dest = backup.create_backup(sample_26bp_path)
    assert dest.exists()
    assert dest.stat().st_size > 0
    assert dest.parent.name == ".backup"
    assert _sha(dest) == _sha(sample_26bp_path)


def test_create_backup_missing_source(tmp_path: Path) -> None:
    with pytest.raises(errors.BackupFailed):
        backup.create_backup(tmp_path / "nope.xlsx")


def test_create_backup_custom_dir(sample_26bp_path: Path, tmp_path: Path) -> None:
    custom = tmp_path / "vault"
    dest = backup.create_backup(sample_26bp_path, backup_dir=custom)
    assert dest.parent == custom
    assert dest.exists()


def test_prune_backups_keeps_n(sample_26bp_path: Path, tmp_path: Path) -> None:
    base = tmp_path / "bk"
    base.mkdir()
    for i in range(15):
        p = base / f"file_{i:02d}.xlsx"
        p.write_bytes(b"x")
    removed = backup.prune_backups(base, keep=10)
    assert removed == 5
    assert len(list(base.glob("*.xlsx"))) == 10
