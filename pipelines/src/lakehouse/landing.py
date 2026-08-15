from dataclasses import dataclass
from typing import Callable

MANIFEST_VERSION = "1.0.0"


@dataclass(frozen=True)
class RunPaths:
    bucket: str
    table: str
    extract_date: str
    run_id: str

    def run_prefix(self) -> str:
        return f"landing/oltp/{self.table}/extract_date={self.extract_date}/run_id={self.run_id}"

    def manifest_key(self) -> str:
        return f"{self.run_prefix()}/manifest.json"

    def data_prefix(self) -> str:
        return f"{self.run_prefix()}/data"


@dataclass(frozen=True)
class ManifestFile:
    path: str
    rows: int
    md5: str


@dataclass(frozen=True)
class Manifest:
    manifest_version: str
    run_id: str
    table: str
    source_system: str
    source_schema: str
    cursor_field: str
    committed_at: str | None
    committed_pk: int | None
    high_watermark_at: str
    high_watermark_pk: int | None
    min_at: str | None
    max_at: str | None
    rows: int
    empty: bool
    files: tuple[ManifestFile, ...]
    generated_at_utc: str


def manifest_from_dict(raw: dict) -> Manifest:
    try:
        source = raw["source"]
        cursor = raw["cursor"]
        return Manifest(
            manifest_version=raw["manifest_version"],
            run_id=raw["run_id"],
            table=raw["table"],
            source_system=source["system"],
            source_schema=source["schema"],
            cursor_field=cursor["field"],
            committed_at=cursor.get("committed_at"),
            committed_pk=cursor.get("committed_pk"),
            high_watermark_at=cursor["high_watermark_at"],
            high_watermark_pk=cursor.get("high_watermark_pk"),
            min_at=cursor.get("min_at"),
            max_at=cursor.get("max_at"),
            rows=raw["rows"],
            empty=raw["empty"],
            files=tuple(ManifestFile(**f) for f in raw.get("files", [])),
            generated_at_utc=raw["generated_at_utc"],
        )
    except KeyError as exc:
        raise ValueError(f"manifest missing key: {exc.args[0]}") from exc


def validate_manifest(
    manifest: Manifest, file_stats: Callable[[str], tuple[int, int] | None]
) -> list[str]:
    violations: list[str] = []
    if manifest.empty:
        if manifest.files:
            violations.append("empty manifest must not list files")
        return violations
    if not manifest.files:
        violations.append("non-empty manifest lists no files")
        return violations
    total_rows = 0
    for f in manifest.files:
        stats = file_stats(f.path)
        if stats is None:
            violations.append(f"missing object: {f.path}")
            continue
        size, rows = stats
        if size <= 0:
            violations.append(f"empty object: {f.path}")
        if rows != f.rows:
            violations.append(f"row mismatch for {f.path}: manifest={f.rows} actual={rows}")
        total_rows += rows
    if total_rows != manifest.rows:
        violations.append(f"total rows mismatch: manifest={manifest.rows} actual={total_rows}")
    if manifest.committed_at is not None and manifest.min_at is not None:
        if manifest.min_at < manifest.committed_at:
            violations.append("min_at is before committed_at")
    if manifest.max_at is not None and manifest.max_at > manifest.high_watermark_at:
        violations.append("max_at is after high_watermark_at")
    return violations