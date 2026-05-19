"""Backup with sha256 verification. Always-on for write tools."""

from __future__ import annotations

import hashlib
import shutil
from datetime import datetime
from pathlib import Path

from . import errors


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def create_backup(file_path: str | Path, *, backup_dir: str | Path | None = None) -> Path:
    src = Path(file_path)
    if not src.exists():
        raise errors.BackupFailed(f"백업 생성 실패: 원본 파일이 없습니다 ({src})")

    base = Path(backup_dir) if backup_dir else src.parent / ".backup"
    try:
        base.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise errors.BackupFailed(f"백업 생성 실패: 디렉터리 생성 실패 — {exc}") from exc

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = base / f"{src.stem}_{ts}{src.suffix}"

    try:
        shutil.copy2(src, dest)
    except OSError as exc:
        raise errors.BackupFailed(f"백업 생성 실패: 복사 오류 — {exc}") from exc

    if not dest.exists() or dest.stat().st_size == 0:
        raise errors.BackupFailed("백업 생성 실패: 결과 파일 크기 0")

    if _sha256(src) != _sha256(dest):
        raise errors.BackupFailed("백업 생성 실패: sha256 불일치")

    return dest


def prune_backups(backup_dir: str | Path, *, keep: int = 10) -> int:
    """Delete oldest backups beyond `keep`. Returns count deleted."""
    base = Path(backup_dir)
    if not base.exists():
        return 0
    files = sorted(base.glob("*.xlsx"), key=lambda p: p.stat().st_mtime, reverse=True)
    removed = 0
    for f in files[keep:]:
        try:
            f.unlink()
            removed += 1
        except OSError:
            pass
    return removed
