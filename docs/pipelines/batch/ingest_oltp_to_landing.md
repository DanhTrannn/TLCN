# Kế hoạch triển khai OLTP Extract → Landing (Section 3)

> **Dành cho agent triển khai:** BẮT BUỘC dùng sub-skill: superpowers:subagent-driven-development (khuyến nghị) hoặc superpowers:executing-plans để thực hiện plan theo từng task. Các bước dùng cú pháp checkbox (`- [ ]`) để theo dõi tiến độ.

**Mục tiêu:** Dựng nửa đầu DAG `ingest_oltp_batch` — trích 16 bảng MySQL thành Parquet bất biến trên MinIO Landing kèm manifest từng bảng, cursor state trên MinIO, và validate manifest — chứng minh cơ chế incremental (predicate composite + boundary + empty run) chỉ lấy đúng dữ liệu mới. Lưu ý theo spec (§10.3): pipeline CHƯA ghi cursor ở Section 3 (commit cursor sau khi Silver publish — Section 5); incremental được chứng minh bằng cursor fixture thủ công viết tạm rồi dọn dẹp.

**Kiến trúc:** Một Spark app chạy trong container Airflow và submit tới `spark://spark-master:7077`; driver của nó đọc committed cursor từ `state/cursor/<table>.json` trên MinIO, đọc từng bảng từ MySQL qua JDBC bằng composite cursor `(cursor_field, pk)` từ catalogue Section 2, ghi Parquet tới `landing/oltp/<table>/extract_date=YYYY-MM-DD/run_id=<run_id>/`, tính md5 từng file, và ghi `manifest.json` **cuối cùng**. Một bước validate bằng Python (boto3 + pyarrow đếm row từ footer) kiểm tra mọi manifest so với object thật. Các PythonOperator trong Airflow lo việc check MySQL, chụp high watermark và validate; chỉ riêng extract là Spark job.

**Tech Stack:** Apache Spark 3.5.9 (pyspark, submit từ airflow image), MySQL 8.4 (JDBC qua mysql-connector-j 8.4.0), MinIO (s3a), Airflow 2.10.5 (SparkSubmitOperator + PythonOperator), boto3, pyarrow, pytest.

**Spec:** theo các quyết định đã chốt trong phiên: D1 = cursor JSON trên MinIO (`state/cursor/<table>.json`); D3 = 1 Spark app, `ThreadPoolExecutor(max_workers=4)` đọc song song 4 bảng, fail-fast; D5 = validate trong Airflow PythonOperator bằng boto3 list + pyarrow đếm row từ footer (không khởi động Spark). Tài liệu tham chiếu: `docs/project/lakehouse-plan.md` §5.2 (layout), §6.1 (Landing), §7.1 (DAG), `docs/project/scope.md` §10.1-10.4 (cursor/mutability/source metadata).

## Ràng buộc toàn cục

- Python `>=3.11,<3.12`; package `batch-pipeline` nằm tại `pipelines/`, các dependency pin đúng phiên bản (theo style hiện có: `PyYAML==6.0.2`, `pytest==8.4.1` trong dev extra).
- Mọi timestamp lưu trữ đều là UTC; timezone nghiệp vụ không bao giờ dùng trong path lưu trữ.
- Landing append-only và bất biến theo object identity nguồn: không bao giờ overwrite hay xóa object Parquet đã ghi. `run_id` là `uuid4().hex` mới cho mỗi lần chạy task extract.
- Định dạng path (chính xác, từ `lakehouse-plan.md` §5.2): `landing/oltp/<table>/extract_date=YYYY-MM-DD/run_id=<run_id>/<file>.parquet` và manifest tại `landing/oltp/<table>/extract_date=YYYY-MM-DD/run_id=<run_id>/manifest.json`.
- Điều kiện cursor (§10.2): predicate incremental `cursor_field > :committed_at OR (cursor_field = :committed_at AND pk > :committed_pk)`; ORDER BY cursor_field, pk.
- Cột metadata nguồn trên mọi row extract (§10.4): `_run_id`, `_source_system`, `_source_schema`, `_source_table`, `_source_primary_key`, `_source_cursor_at`, `_source_high_watermark`, `_ingested_at_utc`.
- Chỉ dùng credential `ecommerce_de_reader` (read-only) cho MySQL. Không bao giờ đọc bảng nào ngoài 16 bảng trong catalogue; không bao giờ đụng tới `customer_credentials`.
- Chạy test bên trong container airflow: `docker compose --profile batch exec -e PYTHONPATH=/opt/project/pipelines/src airflow-scheduler python -m pytest /opt/project/pipelines/tests -q` (chỉ test python thuần — không dùng Spark trong unit test).
- Commit sau mỗi task trên nhánh `dev`. Style message: `feat(pipelines): ...` / `fix(...)`.
- Biến môi trường đã có sẵn trong airflow-common (đã set trong `docker-compose.yml`): `MYSQL_ECOMMERCE_READER_URL`, `MINIO_ENDPOINT`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, `MINIO_LAKEHOUSE_BUCKET`, `PIPELINE_CONFIG_PATH`, `PIPELINE_RUN_DIRECTORY`, `SPARK_MASTER_URL`, `POLARIS_CATALOG_URI`, `POLARIS_CREDENTIAL_FILE`, `POLARIS_CATALOG_NAME`.

## Cấu trúc file

```
pipelines/
├── pyproject.toml                          # SỬA Task 1: + pymysql, boto3, pyarrow
├── src/lakehouse/
│   ├── config.py                           # có sẵn (Section 2): load_config(), Config, TableSpec, RunSpec
│   ├── spark.py                            # SỬA Task 4: + cấu hình S3A trong spark_session()
│   ├── cursor.py                           # TẠO MỚI Task 2: CursorState + JSON round-trip
│   ├── landing.py                          # TẠO MỚI Task 3: path builder + Manifest + validate_manifest
│   ├── extract.py                          # TẠO MỚI Task 5: extract 1 bảng + orchestrator song song
│   ├── validate.py                         # TẠO MỚI Task 6: validate manifest bằng boto3 + pyarrow
│   └── jobs/
│       └── extract_oltp.py                 # TẠO MỚI Task 5: entrypoint spark-submit
├── tests/
│   ├── test_config.py                      # có sẵn (Section 2)
│   ├── test_cursor.py                      # TẠO MỚI Task 2
│   ├── test_landing.py                     # TẠO MỚI Task 3
│   └── test_validate.py                    # TẠO MỚI Task 6
airflow/dags/ingest_oltp_batch.py           # TẠO MỚI Task 7: DAG
docker-compose.yml                          # SỬA Task 1: bucket default web-lakehouse
```

---

### Task 1: Thêm dependency Python (pymysql, boto3, pyarrow) và sửa bucket default

**Files:**
- Sửa: `pipelines/pyproject.toml` (block dependencies)
- Sửa: `docker-compose.yml` (5 chỗ `:-lakehouse`)
- Test: không có (xác nhận bằng rebuild + check import)

**Interfaces:**
- Tạo ra: airflow image chứa `pymysql`, `boto3`, `pyarrow` (chúng vào image qua `uv export` các member của workspace — airflow Dockerfile đã chạy lệnh này); compose bucket default `web-lakehouse` khớp `.env` và `lakehouse-plan.md`.

- [ ] **Bước 1: Thêm dependency vào `pipelines/pyproject.toml`**

```toml
dependencies = [
  "PyYAML==6.0.2",
  "pymysql==1.1.1",
  "boto3==1.35.99",
  "pyarrow==17.0.0",
]
```

- [ ] **Bước 2: Sửa bucket default trong `docker-compose.yml`**

Thay mọi `${MINIO_LAKEHOUSE_BUCKET:-lakehouse}` thành `${MINIO_LAKEHOUSE_BUCKET:-web-lakehouse}` (các chỗ gần dòng 25, 210, 224, 328, 329 — giữ nguyên tên biến env).

- [ ] **Bước 3: Regenerate lockfile**

Chạy: `uv lock`
Kỳ vọng: resolve 48+ packages, có entry pymysql/boto3/pyarrow.

- [ ] **Bước 4: Rebuild airflow image và verify imports**

```bash
docker compose --profile batch build airflow-init 2>&1 | tail -2
docker compose --profile batch up -d airflow-init airflow-scheduler airflow-webserver
docker compose --profile batch exec airflow-scheduler python -c \
  "import pymysql, boto3, pyarrow; print('deps OK', pyarrow.__version__)"
```

Kỳ vọng: `deps OK 17.0.0`.

- [ ] **Bước 5: Commit**

```bash
git add pipelines/pyproject.toml uv.lock docker-compose.yml
git commit -m "feat(pipelines): add pymysql boto3 pyarrow deps and fix lakehouse bucket default"
```

---

### Task 2: `cursor.py` — mô hình cursor state đã commit

**Files:**
- Tạo mới: `pipelines/src/lakehouse/cursor.py`
- Test: `pipelines/tests/test_cursor.py`

**Interfaces:**
- `CURSOR_DIR = "state/cursor"` (hằng module)
- `@dataclass(frozen=True) CursorState: cursor_at: str; cursor_pk: int | None; updated_at_utc: str`
- `cursor_object_path(bucket: str, table: str) -> str` → `state/cursor/<table>.json`
- `CursorState.from_json(text: str) -> CursorState` — raise `ValueError` khi thiếu/sai field
- `CursorState.to_json(self) -> str`
- Tiêu thụ: không (stdlib thuần); sau này `extract.py` (Task 5) dùng.

- [ ] **Bước 1: Viết test (sẽ fail)**

```python
import json

import pytest

from lakehouse.cursor import CURSOR_DIR, CursorState, cursor_object_path


def test_cursor_object_path():
    assert cursor_object_path("web-lakehouse", "orders") == "state/cursor/orders.json"


def test_to_json_round_trip():
    state = CursorState(cursor_at="2026-08-15T10:00:00.000000", cursor_pk=42,
                        updated_at_utc="2026-08-15T10:05:00Z")
    parsed = CursorState.from_json(state.to_json())
    assert parsed == state


def test_from_json_accepts_null_pk():
    state = CursorState.from_json(json.dumps(
        {"cursor_at": "2026-08-15T10:00:00.000000", "cursor_pk": None,
         "updated_at_utc": "2026-08-15T10:05:00Z"}))
    assert state.cursor_pk is None


def test_from_json_missing_field_raises():
    with pytest.raises(ValueError, match="cursor_at"):
        CursorState.from_json('{"cursor_pk": 1, "updated_at_utc": "x"}')


def test_from_json_bad_pk_raises():
    with pytest.raises(ValueError, match="cursor_pk"):
        CursorState.from_json('{"cursor_at": "x", "cursor_pk": "abc", "updated_at_utc": "y"}')


def test_cursor_dir_constant():
    assert CURSOR_DIR == "state/cursor"
```

- [ ] **Bước 2: Chạy test để xác nhận fail**

Chạy: `docker compose --profile batch exec -e PYTHONPATH=/opt/project/pipelines/src airflow-scheduler python -m pytest /opt/project/pipelines/tests/test_cursor.py -q`
Kỳ vọng: FAIL — `ModuleNotFoundError: No module named 'lakehouse.cursor'`

- [ ] **Bước 3: Viết implementation**

```python
import json
from dataclasses import asdict, dataclass

CURSOR_DIR = "state/cursor"


def cursor_object_path(bucket: str, table: str) -> str:
    return f"{CURSOR_DIR}/{table}.json"


@dataclass(frozen=True)
class CursorState:
    cursor_at: str
    cursor_pk: int | None
    updated_at_utc: str

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, text: str) -> "CursorState":
        raw = json.loads(text)
        if "cursor_at" not in raw:
            raise ValueError("cursor_at is required")
        pk = raw.get("cursor_pk")
        if pk is not None and not isinstance(pk, int):
            raise ValueError("cursor_pk must be an int or null")
        if "updated_at_utc" not in raw:
            raise ValueError("updated_at_utc is required")
        return cls(cursor_at=raw["cursor_at"], cursor_pk=pk, updated_at_utc=raw["updated_at_utc"])
```

- [ ] **Bước 4: Chạy test để xác nhận pass**

Chạy: cùng lệnh pytest ở Bước 2
Kỳ vọng: `6 passed`

- [ ] **Bước 5: Commit**

```bash
git add pipelines/src/lakehouse/cursor.py pipelines/tests/test_cursor.py
git commit -m "feat(pipelines): add committed cursor state model"
```

---

### Task 3: `landing.py` — run paths và mô hình manifest

**Files:**
- Tạo mới: `pipelines/src/lakehouse/landing.py`
- Test: `pipelines/tests/test_landing.py`

**Interfaces:**
- `RunPaths` dataclass: `bucket: str; table: str; extract_date: str; run_id: str` với:
  - `run_prefix(self) -> str` → `landing/oltp/<table>/extract_date=<date>/run_id=<run_id>`
  - `manifest_key(self) -> str` → `<run_prefix>/manifest.json`
  - `data_prefix(self) -> str` → `<run_prefix>/data`
- `Manifest` dataclass (frozen): `manifest_version: str; run_id: str; table: str; source_system: str; source_schema: str; cursor_field: str; committed_at: str | None; committed_pk: int | None; high_watermark_at: str; high_watermark_pk: int | None; min_at: str | None; max_at: str | None; rows: int; empty: bool; files: tuple[ManifestFile, ...]; generated_at_utc: str`
- `ManifestFile` dataclass (frozen): `path: str; rows: int; md5: str`
- `manifest_from_dict(raw: dict) -> Manifest` (validate key bắt buộc; raise `ValueError`)
- `validate_manifest(manifest: Manifest, file_stats: Callable[[str], tuple[int, int]]) -> list[str]` — logic thuần, trả danh sách vi phạm (rỗng = hợp lệ). `file_stats(path)` trả `(size_bytes, row_count)` của object thật; chỉ gọi cho `manifest.files`.
  Kiểm tra: manifest empty phải có 0 file; non-empty phải có ≥1 file; mỗi file tồn tại (stats != None) với size > 0 và rows khớp; tổng file rows == manifest.rows; cursor: nếu `committed_at` có giá trị thì `min_at >= committed_at`; `max_at <= high_watermark_at`.

- [ ] **Bước 1: Viết test (sẽ fail)**

```python
import pytest

from lakehouse.landing import RunPaths, manifest_from_dict, validate_manifest

RUN = RunPaths(bucket="web-lakehouse", table="orders",
               extract_date="2026-08-15", run_id="run123")


def test_run_prefix():
    assert RUN.run_prefix() == "landing/oltp/orders/extract_date=2026-08-15/run_id=run123"


def test_manifest_key_and_data_prefix():
    assert RUN.manifest_key() == "landing/oltp/orders/extract_date=2026-08-15/run_id=run123/manifest.json"
    assert RUN.data_prefix() == "landing/oltp/orders/extract_date=2026-08-15/run_id=run123/data"


def test_manifest_from_dict_round_trip():
    raw = {
        "manifest_version": "1.0.0", "run_id": "run123", "table": "orders",
        "source": {"system": "mysql_ecommerce", "schema": "ecommerce"},
        "cursor": {"field": "updated_at", "committed_at": "2026-08-15T09:00:00",
                   "committed_pk": 1, "high_watermark_at": "2026-08-15T10:00:00",
                   "high_watermark_pk": 5, "min_at": "2026-08-15T09:01:00",
                   "max_at": "2026-08-15T10:00:00"},
        "rows": 4, "empty": False,
        "files": [{"path": "s3://x/data/p1.parquet", "rows": 2, "md5": "a"},
                  {"path": "s3://x/data/p2.parquet", "rows": 2, "md5": "b"}],
        "generated_at_utc": "2026-08-15T10:05:00Z",
    }
    manifest = manifest_from_dict(raw)
    assert manifest.rows == 4
    assert manifest.files[1].md5 == "b"
    assert manifest.cursor_field == "updated_at"


def test_manifest_from_dict_missing_required_key_raises():
    with pytest.raises(ValueError, match="source"):
        manifest_from_dict({"run_id": "r"})


def test_validate_manifest_ok():
    raw = {
        "manifest_version": "1.0.0", "run_id": "run123", "table": "orders",
        "source": {"system": "mysql_ecommerce", "schema": "ecommerce"},
        "cursor": {"field": "updated_at", "committed_at": "2026-08-15T09:00:00",
                   "committed_pk": 1, "high_watermark_at": "2026-08-15T10:00:00",
                   "high_watermark_pk": 5, "min_at": "2026-08-15T09:01:00",
                   "max_at": "2026-08-15T10:00:00"},
        "rows": 4, "empty": False,
        "files": [{"path": "p1", "rows": 2, "md5": "a"},
                  {"path": "p2", "rows": 2, "md5": "b"}],
        "generated_at_utc": "2026-08-15T10:05:00Z",
    }
    manifest = manifest_from_dict(raw)
    stats = {"p1": (100, 2), "p2": (100, 2)}
    assert validate_manifest(manifest, lambda p: stats.get(p)) == []


def test_validate_manifest_row_mismatch_reported():
    raw = {
        "manifest_version": "1.0.0", "run_id": "run123", "table": "orders",
        "source": {"system": "mysql_ecommerce", "schema": "ecommerce"},
        "cursor": {"field": "updated_at", "committed_at": None, "committed_pk": None,
                   "high_watermark_at": "2026-08-15T10:00:00", "high_watermark_pk": 5,
                   "min_at": None, "max_at": None},
        "rows": 4, "empty": False,
        "files": [{"path": "p1", "rows": 2, "md5": "a"}],
        "generated_at_utc": "2026-08-15T10:05:00Z",
    }
    manifest = manifest_from_dict(raw)
    stats = {"p1": (100, 1)}
    violations = validate_manifest(manifest, lambda p: stats.get(p))
    assert any("p1" in v and "row" in v for v in violations)
    assert any("rows" in v for v in violations)


def test_validate_manifest_missing_file_reported():
    raw = {
        "manifest_version": "1.0.0", "run_id": "run123", "table": "orders",
        "source": {"system": "mysql_ecommerce", "schema": "ecommerce"},
        "cursor": {"field": "updated_at", "committed_at": None, "committed_pk": None,
                   "high_watermark_at": "2026-08-15T10:00:00", "high_watermark_pk": 5,
                   "min_at": None, "max_at": None},
        "rows": 2, "empty": False,
        "files": [{"path": "p1", "rows": 2, "md5": "a"}],
        "generated_at_utc": "2026-08-15T10:05:00Z",
    }
    manifest = manifest_from_dict(raw)
    violations = validate_manifest(manifest, lambda p: None)
    assert any("missing" in v for v in violations)


def test_validate_manifest_empty_requires_no_files():
    raw = {
        "manifest_version": "1.0.0", "run_id": "run123", "table": "orders",
        "source": {"system": "mysql_ecommerce", "schema": "ecommerce"},
        "cursor": {"field": "updated_at", "committed_at": "2026-08-15T09:00:00",
                   "committed_pk": 1, "high_watermark_at": "2026-08-15T10:00:00",
                   "high_watermark_pk": 5, "min_at": None, "max_at": None},
        "rows": 0, "empty": True, "files": [],
        "generated_at_utc": "2026-08-15T10:05:00Z",
    }
    manifest = manifest_from_dict(raw)
    assert validate_manifest(manifest, lambda p: None) == []


def test_validate_manifest_cursor_range_ok_skipped_when_committed_null():
    raw = {
        "manifest_version": "1.0.0", "run_id": "run123", "table": "orders",
        "source": {"system": "mysql_ecommerce", "schema": "ecommerce"},
        "cursor": {"field": "updated_at", "committed_at": None, "committed_pk": None,
                   "high_watermark_at": "2026-08-15T10:00:00", "high_watermark_pk": 5,
                   "min_at": "2026-08-15T09:01:00", "max_at": "2026-08-15T10:00:00"},
        "rows": 2, "empty": False,
        "files": [{"path": "p1", "rows": 2, "md5": "a"}],
        "generated_at_utc": "2026-08-15T10:05:00Z",
    }
    manifest = manifest_from_dict(raw)
    assert validate_manifest(manifest, lambda p: (100, 2)) == []
```

- [ ] **Bước 2: Chạy test để xác nhận fail**

Chạy: `docker compose --profile batch exec -e PYTHONPATH=/opt/project/pipelines/src airflow-scheduler python -m pytest /opt/project/pipelines/tests/test_landing.py -q`
Kỳ vọng: FAIL — `ModuleNotFoundError: No module named 'lakehouse.landing'`

- [ ] **Bước 3: Viết implementation**

```python
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
```

- [ ] **Bước 4: Chạy test để xác nhận pass**

Chạy: cùng lệnh pytest ở Bước 2
Kỳ vọng: `9 passed`

- [ ] **Bước 5: Commit**

```bash
git add pipelines/src/lakehouse/landing.py pipelines/tests/test_landing.py
git commit -m "feat(pipelines): add landing run paths and manifest model"
```

---

### Task 4: Cấu hình S3A trong `spark.py` (ghi s3a trực tiếp vào MinIO)

**Files:**
- Sửa: `pipelines/src/lakehouse/spark.py` (thêm một hàm)
- Test: không có (unit-test builder không có ý nghĩa; xác nhận bằng integration ở Task 5)

**Interfaces:**
- `configure_s3a(builder) -> builder` — thêm các key `spark.hadoop.fs.s3a.*` từ env: `MINIO_ENDPOINT` → `fs.s3a.endpoint`, `MINIO_ACCESS_KEY` → `fs.s3a.access.key`, `MINIO_SECRET_KEY` → `fs.s3a.secret.key`, kèm `fs.s3a.path.style.access=true`, `fs.s3a.connection.ssl.enabled=false` (endpoint http), `fs.s3a.impl=org.apache.hadoop.fs.s3a.S3AFileSystem`.
- `spark_session(job_name)` gọi `configure_s3a` trên builder trước `getOrCreate()`.
- Tiêu thụ: các env đã set trong airflow-common.

- [ ] **Bước 1: Sửa `spark.py`**

Thêm trước `spark_session` (và gọi trong `spark_session`):

```python
def configure_s3a(builder):
    return (
        builder
        .config("spark.hadoop.fs.s3a.endpoint", os.environ["MINIO_ENDPOINT"])
        .config("spark.hadoop.fs.s3a.access.key", os.environ["MINIO_ACCESS_KEY"])
        .config("spark.hadoop.fs.s3a.secret.key", os.environ["MINIO_SECRET_KEY"])
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    )
```

Rồi trong `spark_session`, thay `return builder.getOrCreate()` bằng:

```python
    return configure_s3a(builder).getOrCreate()
```

- [ ] **Bước 2: Sanity-check file vẫn import được**

Chạy: `docker compose --profile batch exec airflow-scheduler python -c "import lakehouse.spark; print('ok')"`
Kỳ vọng: `ok`

- [ ] **Bước 3: Commit**

```bash
git add pipelines/src/lakehouse/spark.py
git commit -m "feat(pipelines): configure s3a filesystem from env for raw landing writes"
```

---

### Task 5: `extract.py` + `jobs/extract_oltp.py` — Spark app extract

**Files:**
- Tạo mới: `pipelines/src/lakehouse/extract.py`
- Tạo mới: `pipelines/src/lakehouse/jobs/extract_oltp.py`
- Test: không có unit-level (cần Spark); xác nhận bằng integration run ở Bước 5

**Interfaces:**
- Tiêu thụ: `config.load_config(path)`, `config.table(name)`, `spark.spark_session(job_name)`, `spark.jdbc_url()`, `cursor.CursorState`, `landing.RunPaths`, `landing.MANIFEST_VERSION`.
- `read_committed_cursor(spark, bucket: str, table: str) -> CursorState | None` — đọc `state/cursor/<table>.json` qua `spark.read.text`; trả `None` khi object không tồn tại.
- `extract_one_table(spark, cfg: Config, table: TableSpec, run_id: str, extract_date: str, high_watermark_at: str, high_watermark_pk: int | None, committed: CursorState | None) -> dict` — trả dict manifest (đúng shape như test Task 3). Raise `RuntimeError` khi lỗi.
- `run_extract(spark, cfg, high_watermarks: dict[str, dict], run_id: str, extract_date: str, max_workers: int) -> list[dict]` — `ThreadPoolExecutor(max_workers=…)`, mỗi worker 1 bảng, fail-fast: exception đầu tiên hủy các future còn lại và được re-raise.
- Entrypoint `jobs/extract_oltp.py`: `main()` parse `--config-path`, `--run-id`, `--extract-date`, `--high-watermarks` (chuỗi JSON `{table: {"at": str, "pk": int|null}}`), load config, gọi `run_extract`, in `EXTRACT OK: <table> rows=<n>` cho từng bảng.

- [ ] **Bước 1: Viết code integration — `extract.py`**

```python
import concurrent.futures
import hashlib
import json
from datetime import datetime, timezone

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, lit, max, min

from lakehouse.config import Config, TableSpec
from lakehouse.cursor import CursorState
from lakehouse.landing import MANIFEST_VERSION, RunPaths


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _hadoop_fs(spark):
    return spark._jvm.org.apache.hadoop.fs.FileSystem.get(
        spark._jsc.hadoopConfiguration()
    )


def read_committed_cursor(spark, bucket: str, table: str) -> CursorState | None:
    path = f"s3a://{bucket}/state/cursor/{table}.json"
    fs = _hadoop_fs(spark)
    if not fs.exists(spark._jvm.org.apache.hadoop.fs.Path(path)):
        return None
    row = spark.read.text(path).first()
    return CursorState.from_json(row["value"])


def _write_manifest(spark, bucket: str, manifest_key: str, manifest: dict) -> None:
    fs = _hadoop_fs(spark)
    path = spark._jvm.org.apache.hadoop.fs.Path(f"s3a://{bucket}/{manifest_key}")
    fs.mkdirs(path.getParent())
    out = fs.create(path, True)
    out.write(json.dumps(manifest).encode("utf-8"))
    out.close()


def _file_stats(spark, paths: RunPaths) -> list[dict]:
    fs = _hadoop_fs(spark)
    glob = f"s3a://{paths.bucket}/{paths.data_prefix()}/*.parquet"
    statuses = sorted(
        fs.globStatus(spark._jvm.org.apache.hadoop.fs.Path(glob)),
        key=lambda s: str(s.getPath()),
    )
    files = []
    for status in statuses:
        key = str(status.getPath()).replace(f"s3a://{paths.bucket}/", "")
        content = spark.read.format("binaryFile").load(
            f"s3a://{paths.bucket}/{key}"
        ).first()["content"]
        md5 = hashlib.md5(bytes(content)).hexdigest()
        rows = int(spark.read.parquet(f"s3a://{paths.bucket}/{key}").count())
        files.append({"path": key, "rows": rows, "md5": md5})
    return files


def extract_one_table(
    spark: SparkSession,
    cfg: Config,
    table: TableSpec,
    run_id: str,
    extract_date: str,
    high_watermark_at: str,
    high_watermark_pk: int | None,
    committed: CursorState | None,
) -> dict:
    paths = RunPaths(bucket=cfg.bucket, table=table.name,
                     extract_date=extract_date, run_id=run_id)
    now_utc = _utc_now()

    range_pred = ""
    if committed is not None:
        range_pred = (
            f" WHERE (`{table.cursor_field}` > '{committed.cursor_at}' OR "
            f"(`{table.cursor_field}` = '{committed.cursor_at}' AND "
            f"`{table.pk}` > {committed.cursor_pk or 0}))"
        )

    bounds = spark.read.format("jdbc").options(
        url=cfg.jdbc_url,
        query=(
            f"SELECT MIN(`{table.pk}`) AS lo, MAX(`{table.pk}`) AS hi "
            f"FROM `{table.name}`{range_pred}"
        ),
    ).load().first()

    cursor_brief = {
        "field": table.cursor_field,
        "committed_at": committed.cursor_at if committed else None,
        "committed_pk": committed.cursor_pk if committed else None,
        "high_watermark_at": high_watermark_at,
        "high_watermark_pk": high_watermark_pk,
        "min_at": None,
        "max_at": None,
    }
    if bounds["lo"] is None:
        manifest = {
            "manifest_version": MANIFEST_VERSION, "run_id": run_id,
            "table": table.name,
            "source": {"system": "mysql_ecommerce", "schema": "ecommerce"},
            "cursor": cursor_brief,
            "rows": 0, "empty": True, "files": [],
            "generated_at_utc": now_utc,
        }
        _write_manifest(spark, paths.bucket, paths.manifest_key(), manifest)
        return manifest

    df = (
        spark.read.format("jdbc")
        .option("url", cfg.jdbc_url)
        .option("query", f"SELECT * FROM `{table.name}`{range_pred}")
        .option("partitionColumn", table.pk)
        .option("lowerBound", str(bounds["lo"]))
        .option("upperBound", str(bounds["hi"] + 1))
        .option("numPartitions", 4)
        .load()
        .orderBy(table.cursor_field, table.pk)
        .withColumn("_run_id", lit(run_id))
        .withColumn("_source_system", lit("mysql_ecommerce"))
        .withColumn("_source_schema", lit("ecommerce"))
        .withColumn("_source_table", lit(table.name))
        .withColumn("_source_primary_key", col(table.pk).cast("string"))
        .withColumn("_source_cursor_at", col(table.cursor_field))
        .withColumn("_source_high_watermark", lit(high_watermark_at))
        .withColumn("_ingested_at_utc", lit(now_utc))
    )

    df.write.mode("overwrite").parquet(
        f"s3a://{paths.bucket}/{paths.data_prefix()}"
    )
    files = _file_stats(spark, paths)

    cursor_df = df.agg(
        min(col(table.cursor_field)).alias("min_at"),
        max(col(table.cursor_field)).alias("max_at"),
        count("*").alias("row_count"),
    ).first()
    cursor_brief["min_at"] = str(cursor_df["min_at"])
    cursor_brief["max_at"] = str(cursor_df["max_at"])

    manifest = {
        "manifest_version": MANIFEST_VERSION, "run_id": run_id,
        "table": table.name,
        "source": {"system": "mysql_ecommerce", "schema": "ecommerce"},
        "cursor": cursor_brief,
        "rows": int(cursor_df["row_count"]),
        "empty": False, "files": files,
        "generated_at_utc": now_utc,
    }
    _write_manifest(spark, paths.bucket, paths.manifest_key(), manifest)
    return manifest


def run_extract(
    spark: SparkSession,
    cfg: Config,
    high_watermarks: dict[str, dict],
    run_id: str,
    extract_date: str,
    max_workers: int,
) -> list[dict]:
    def worker(table: TableSpec) -> dict:
        hw = high_watermarks.get(table.name)
        if hw is None:
            raise RuntimeError(f"no high watermark captured for {table.name}")
        committed = read_committed_cursor(spark, cfg.bucket, table.name)
        return extract_one_table(
            spark, cfg, table, run_id, extract_date,
            high_watermark_at=hw["at"], high_watermark_pk=hw.get("pk"),
            committed=committed,
        )

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(worker, table): table.name for table in cfg.tables}
        manifests = []
        for future in concurrent.futures.as_completed(futures):
            try:
                manifests.append(future.result())
            except Exception:
                for other in futures:
                    other.cancel()
                raise
    return manifests
```

- [ ] **Bước 2: Viết entrypoint `jobs/extract_oltp.py`**

```python
import argparse
import json

from lakehouse.config import load_config
from lakehouse.extract import run_extract
from lakehouse.spark import spark_session


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract OLTP tables to MinIO landing")
    parser.add_argument("--config-path", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--extract-date", required=True)
    parser.add_argument("--high-watermarks", required=True)
    args = parser.parse_args()

    cfg = load_config(args.config_path)
    high_watermarks = json.loads(args.high_watermarks)
    spark = spark_session("extract_oltp_to_landing")
    manifests = run_extract(
        spark, cfg, high_watermarks,
        run_id=args.run_id, extract_date=args.extract_date,
        max_workers=cfg.run.max_parallel_tables,
    )
    for manifest in manifests:
        print(f"EXTRACT OK: {manifest['table']} rows={manifest['rows']} empty={manifest['empty']}")
    spark.stop()


if __name__ == "__main__":
    main()
```

- [ ] **Bước 3: Mở rộng `config.py` (bounded, không đụng catalogue hiện có)**

`Config` trong `pipelines/src/lakehouse/config.py` ĐÃ có sẵn `run`/`landing`/`tables` (Section 2) — chỉ thêm 2 property sau vào class `Config` hiện có (không viết lại class), và thêm field `max_parallel_tables` cho `RunSpec` + key tương ứng trong `default.yml`:

```python
    @property
    def bucket(self) -> str:
        return os.environ["MINIO_LAKEHOUSE_BUCKET"]

    @property
    def jdbc_url(self) -> str:
        from lakehouse.spark import jdbc_url
        return jdbc_url()
```

Sửa `RunSpec` (config.py) thành:

```python
@dataclass(frozen=True)
class RunSpec:
    data_interval_minutes: int
    retries: int
    quarantine_max_rows: int
    max_parallel_tables: int
```

Sửa `pipelines/config/default.yml` phần `run:`:

```yaml
run:
  data_interval_minutes: 15
  retries: 2
  quarantine_max_rows: 100000
  max_parallel_tables: 4
```

- [ ] **Bước 4: Chạy unit tests để xác nhận không hỏng gì**

Chạy: `docker compose --profile batch exec -e PYTHONPATH=/opt/project/pipelines/src airflow-scheduler python -m pytest /opt/project/pipelines/tests -q`
Kỳ vọng: `29 passed` (14 config + 6 cursor + 9 landing)

- [ ] **Bước 5: Integration run — full extract lần đầu (cả 16 bảng)**

`run_extract` fail-fast nếu thiếu high watermark cho bất kỳ bảng nào → phải chụp HW cho CẢ 16 bảng (cùng SQL mà DAG `capture_high_watermarks` dùng), rồi chạy app. Chưa có file cursor nào → đây là full extract (đúng hành vi lần đầu):

```bash
HW_JSON=$(docker compose --profile batch exec -T airflow-scheduler python - <<'EOF'
import json, os
import pymysql
from sqlalchemy.engine.url import make_url
from lakehouse.config import load_config
cfg = load_config(os.environ["PIPELINE_CONFIG_PATH"])
url = make_url(os.environ["MYSQL_ECOMMERCE_READER_URL"])
conn = pymysql.connect(host=url.host, port=url.port or 3306,
                       user=url.username, password=url.password, database=url.database)
result = {}
try:
    with conn.cursor() as cur:
        for t in cfg.tables:
            cur.execute(
                f"SELECT MAX(`{t.cursor_field}`) AS at, MAX(`{t.pk}`) AS pk_at_max "
                f"FROM `{t.name}` WHERE `{t.cursor_field}` = "
                f"(SELECT MAX(`{t.cursor_field}`) FROM `{t.name}`)"
            )
            row = cur.fetchone()
            result[t.name] = {"at": str(row[0]), "pk": row[1]}
finally:
    conn.close()
print(json.dumps(result))
EOF
)
docker compose --profile batch exec airflow-scheduler spark-submit \
  /opt/project/pipelines/src/jobs/extract_oltp.py \
  --config-path /opt/project/pipelines/config/default.yml \
  --run-id testrun1 --extract-date 2026-08-15 \
  --high-watermarks "$HW_JSON"
```

Kỳ vọng: `EXTRACT OK: <table> rows=<n> empty=False` cho cả 16 bảng và object xuất hiện dưới `landing/oltp/<table>/extract_date=2026-08-15/run_id=testrun1/` với `manifest.json` liệt kê các file parquet + md5. Số rows từng bảng phải khớp `SELECT COUNT(*)` tại thời điểm đó (baseline hiện tại: customers=503, orders=3001 — con số chính xác không quan trọng, quan trọng là manifest khớp với thực tế DB).

- [ ] **Bước 6: Commit**

```bash
git add pipelines/src/lakehouse/extract.py pipelines/src/lakehouse/jobs/extract_oltp.py pipelines/src/lakehouse/config.py
git commit -m "feat(pipelines): add parallel OLTP extract spark app with manifests"
```

---

### Task 6: `validate.py` — validate manifest bằng boto3 + pyarrow

**Files:**
- Tạo mới: `pipelines/src/lakehouse/validate.py`
- Test: `pipelines/tests/test_validate.py`

**Interfaces:**
- Tiêu thụ: `landing.validate_manifest`, `landing.manifest_from_dict`, `landing.RunPaths`, `boto3`, `pyarrow.parquet`.
- `s3_client(endpoint: str, access_key: str, secret_key: str)` → boto3 client với `endpoint_url`, `region_name="us-east-1"`, path-style addressing.
- `load_manifest(s3, bucket: str, key: str) -> Manifest` — GET object, parse JSON qua `manifest_from_dict`.
- `parquet_row_count(data: bytes) -> int` — `pq.ParquetFile(io.BytesIO(data)).metadata.num_rows` (chỉ đọc footer, không scan dữ liệu).
- `validate_manifest_on_s3(s3, bucket: str, paths: RunPaths, load_stats: Callable[[str], tuple[int, int] | None] | None = None) -> list[str]` — `load_stats` mặc định = boto3 GET object size + `parquet_row_count`; trả vi phạm qua `validate_manifest`.
- `validate_run(s3, bucket: str, tables: list[str], extract_date: str, run_id: str) -> dict[str, list[str]]` — vi phạm theo từng bảng.

- [ ] **Bước 1: Viết test (sẽ fail)**

```python
import io

import pyarrow as pa
import pyarrow.parquet as pq

from lakehouse.landing import RunPaths
from lakehouse.validate import parquet_row_count, validate_manifest_on_s3


def _make_parquet_bytes(rows: int) -> bytes:
    buf = io.BytesIO()
    pq.write_table(pa.table({"id": list(range(rows))}), buf)
    return buf.getvalue()


def test_parquet_row_count_from_footer():
    assert parquet_row_count(_make_parquet_bytes(7)) == 7


class _FakeS3:
    def __init__(self, objects: dict[str, bytes]):
        self.objects = objects

    def get_object(self, Bucket, Key):
        return {"Body": io.BytesIO(self.objects[Key]), "ContentLength": len(self.objects[Key])}


def test_validate_manifest_on_s3_ok():
    data = _make_parquet_bytes(2)
    s3 = _FakeS3({"p1.parquet": data, "p2.parquet": data})
    raw = {
        "manifest_version": "1.0.0", "run_id": "r1", "table": "orders",
        "source": {"system": "mysql_ecommerce", "schema": "ecommerce"},
        "cursor": {"field": "updated_at", "committed_at": None, "committed_pk": None,
                   "high_watermark_at": "2026-08-15T10:00:00", "high_watermark_pk": 5,
                   "min_at": None, "max_at": None},
        "rows": 4, "empty": False,
        "files": [{"path": "p1.parquet", "rows": 2, "md5": "a"},
                  {"path": "p2.parquet", "rows": 2, "md5": "b"}],
        "generated_at_utc": "2026-08-15T10:05:00Z",
    }
    s3.objects["manifest.json"] = __import__("json").dumps(raw).encode()
    paths = RunPaths(bucket="b", table="orders", extract_date="2026-08-15", run_id="r1")
    violations = validate_manifest_on_s3(
        s3, "b", paths,
        load_stats=lambda key: (
            (len(s3.objects[key]), parquet_row_count(s3.objects[key]))
            if key in s3.objects else None
        ),
    )
    assert violations == []


def test_validate_manifest_on_s3_reports_missing_and_row_mismatch():
    data = _make_parquet_bytes(2)
    s3 = _FakeS3({"p1.parquet": data})
    raw = {
        "manifest_version": "1.0.0", "run_id": "r1", "table": "orders",
        "source": {"system": "mysql_ecommerce", "schema": "ecommerce"},
        "cursor": {"field": "updated_at", "committed_at": None, "committed_pk": None,
                   "high_watermark_at": "2026-08-15T10:00:00", "high_watermark_pk": 5,
                   "min_at": None, "max_at": None},
        "rows": 4, "empty": False,
        "files": [{"path": "p1.parquet", "rows": 2, "md5": "a"},
                  {"path": "p2.parquet", "rows": 3, "md5": "b"}],
        "generated_at_utc": "2026-08-15T10:05:00Z",
    }
    s3.objects["manifest.json"] = __import__("json").dumps(raw).encode()
    paths = RunPaths(bucket="b", table="orders", extract_date="2026-08-15", run_id="r1")
    violations = validate_manifest_on_s3(
        s3, "b", paths,
        load_stats=lambda key: (
            (len(s3.objects[key]), parquet_row_count(s3.objects[key]))
            if key in s3.objects else None
        ),
    )
    assert any("missing" in v for v in violations)
    assert any("row mismatch" in v for v in violations)
```

- [ ] **Bước 2: Chạy test để xác nhận fail**

Chạy: `docker compose --profile batch exec -e PYTHONPATH=/opt/project/pipelines/src airflow-scheduler python -m pytest /opt/project/pipelines/tests/test_validate.py -q`
Kỳ vọng: FAIL — `ModuleNotFoundError: No module named 'lakehouse.validate'`

- [ ] **Bước 3: Viết implementation**

```python
import io
import json
import os

import boto3
import pyarrow.parquet as pq

from lakehouse.landing import Manifest, RunPaths, manifest_from_dict, validate_manifest

S3_REGION = "us-east-1"


def s3_client(endpoint: str, access_key: str, secret_key: str):
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=S3_REGION,
    )


def load_manifest(s3, bucket: str, key: str) -> Manifest:
    body = s3.get_object(Bucket=bucket, Key=key)["Body"].read()
    return manifest_from_dict(json.loads(body))


def parquet_row_count(data: bytes) -> int:
    return pq.ParquetFile(io.BytesIO(data)).metadata.num_rows


def validate_manifest_on_s3(
    s3,
    bucket: str,
    paths: RunPaths,
    load_stats=None,
) -> list[str]:
    manifest = load_manifest(s3, bucket, paths.manifest_key())
    if load_stats is None:
        def load_stats(key: str):
            try:
                obj = s3.get_object(Bucket=bucket, Key=key)
            except Exception:
                return None
            data = obj["Body"].read()
            return len(data), parquet_row_count(data)
    return validate_manifest(manifest, load_stats)


def validate_run(s3, bucket: str, tables: list[str], extract_date: str, run_id: str) -> dict[str, list[str]]:
    violations_by_table: dict[str, list[str]] = {}
    for table in tables:
        paths = RunPaths(bucket=bucket, table=table, extract_date=extract_date, run_id=run_id)
        violations_by_table[table] = validate_manifest_on_s3(s3, bucket, paths)
    return violations_by_table
```

- [ ] **Bước 4: Chạy test để xác nhận pass**

Chạy: cùng lệnh pytest ở Bước 2
Kỳ vọng: `3 passed`

- [ ] **Bước 5: Integration smoke với MinIO**

```bash
docker compose --profile batch exec -T airflow-scheduler python - <<'EOF'
import os
from lakehouse.validate import s3_client, validate_manifest_on_s3
from lakehouse.landing import RunPaths
s3 = s3_client(os.environ["MINIO_ENDPOINT"], os.environ["MINIO_ACCESS_KEY"], os.environ["MINIO_SECRET_KEY"])
paths = RunPaths(bucket=os.environ["MINIO_LAKEHOUSE_BUCKET"], table="customers",
                 extract_date="2026-08-15", run_id="testrun1")
print("violations:", validate_manifest_on_s3(s3, paths.bucket, paths))
EOF
```

Kỳ vọng: `violations: []` (validate manifest đã ghi ở Task 5 Bước 5).

- [ ] **Bước 6: Commit**

```bash
git add pipelines/src/lakehouse/validate.py pipelines/tests/test_validate.py
git commit -m "feat(pipelines): add manifest validation with pyarrow footer row counts"
```

---

### Task 7: DAG `airflow/dags/ingest_oltp_batch.py`

**Files:**
- Tạo mới: `airflow/dags/ingest_oltp_batch.py`
- Test: check DAG parse + integration trigger

**Interfaces:**
- Tiêu thụ: `config.load_config`, `validate.s3_client/validate_run`, `extract` (qua SparkSubmitOperator app path `/opt/project/pipelines/src/jobs/extract_oltp.py`), các env từ airflow-common.
- `check_mysql() -> str` — pymysql connect qua `MYSQL_ECOMMERCE_READER_URL` (dùng `sqlalchemy.engine.url.make_url` để parse), `SELECT 1`; trả `"ok"`. Không nhận arg — D1 là PythonOperator thuần (không dùng BashOperator/mysqladmin ping).
- `begin_run(**context)` — push `run_id = uuid4().hex` và `extract_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")` lên XCom.
- `capture_high_watermarks() -> dict[str, dict]` — mỗi bảng `SELECT MAX(cursor_field) AS at, MAX(pk) AS pk_at_max FROM <table> WHERE cursor_field = (SELECT MAX(cursor_field) FROM <table>)`; trả `{table: {"at": str, "pk": int | None}}`.
- DAG: `dag_id="ingest_oltp_batch"`, `schedule=None`, `catchup=False`, `default_args={"retries": 2, "retry_delay": timedelta(minutes=1)}`, thứ tự task: `check_mysql → begin_run → capture_high_watermarks → extract_tables_to_landing → validate_landing_manifests`.
- `extract_tables_to_landing` dùng `SparkSubmitOperator(application=..., application_args=[...])` với các arg template `{{ ti.xcom_pull(...) }}`. **Không truyền kwarg `master`** — provider `apache-spark 4.11.3` không có kwarg này; master lấy từ connection `spark_default` (host `spark://spark-master:7077`). Connection là DB-backed và phải có khi khởi tạo môi trường:
  `airflow connections add spark_default --conn-host spark://spark-master:7077`
- `validate_landing_manifests` dùng `PythonOperator` gọi `validate_run(...)` và raise `AirflowException` liệt kê vi phạm khi có bất kỳ bảng nào lỗi.

**Ghi chú reconcile (R14/R16) — khớp DAG đã commit (181ec60):**

- D1 `check_mysql` = PythonOperator chạy `SELECT 1` (không phải BashOperator mysqladmin ping); D2 `begin_run` chỉ push XCom `run_id=uuid4().hex` + `extract_date` UTC (không tạo run dir); D3 `capture_high_watermarks` trả dict qua XCom (không ghi `high_watermarks.json`); D4 nhận HW qua `{{ ti.xcom_pull(task_ids='capture_high_watermarks') | tojson }}`.
- `default_args`: `retries=2`, `retry_delay=1min`, `start_date` UTC (không phải `retries=0`).
- Section này KHÔNG ghi `/data/pipeline-runs` (env `PIPELINE_RUN_DIRECTORY` dành cho section sau); verification hoàn toàn qua MinIO manifests (boto3 + pyarrow), không có `metadata.json`.

- [ ] **Bước 1: Viết DAG**

```python
import json
import os
import uuid
from datetime import datetime, timedelta, timezone

import pymysql
from airflow import DAG
from airflow.exceptions import AirflowException
from airflow.operators.python import PythonOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from sqlalchemy.engine.url import make_url

from lakehouse.config import load_config
from lakehouse.validate import s3_client, validate_run

CONFIG_PATH = os.environ["PIPELINE_CONFIG_PATH"]
SPARK_APP = "/opt/project/pipelines/src/jobs/extract_oltp.py"

DEFAULT_ARGS = {
    "owner": "batch",
    "retries": 2,
    "retry_delay": timedelta(minutes=1),
}


def _mysql_conn():
    url = make_url(os.environ["MYSQL_ECOMMERCE_READER_URL"])
    return pymysql.connect(
        host=url.host, port=url.port or 3306, user=url.username,
        password=url.password, database=url.database, connect_timeout=10,
    )


def check_mysql() -> str:
    conn = _mysql_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
    finally:
        conn.close()
    return "ok"


def begin_run(**context) -> None:
    context["ti"].xcom_push(key="run_id", value=uuid.uuid4().hex)
    context["ti"].xcom_push(
        key="extract_date", value=datetime.now(timezone.utc).strftime("%Y-%m-%d")
    )


def capture_high_watermarks() -> dict:
    cfg = load_config(CONFIG_PATH)
    conn = _mysql_conn()
    result = {}
    try:
        with conn.cursor() as cur:
            for table in cfg.tables:
                cur.execute(
                    f"SELECT MAX(`{table.cursor_field}`) AS at, "
                    f"MAX(`{table.pk}`) AS pk_at_max "
                    f"FROM `{table.name}` "
                    f"WHERE `{table.cursor_field}` = "
                    f"(SELECT MAX(`{table.cursor_field}`) FROM `{table.name}`)"
                )
                row = cur.fetchone()
                result[table.name] = {"at": str(row[0]), "pk": row[1]}
    finally:
        conn.close()
    return result


def validate_landing_manifests(**context) -> None:
    cfg = load_config(CONFIG_PATH)
    run_id = context["ti"].xcom_pull(task_ids="begin_run", key="run_id")
    extract_date = context["ti"].xcom_pull(task_ids="begin_run", key="extract_date")
    s3 = s3_client(
        os.environ["MINIO_ENDPOINT"], os.environ["MINIO_ACCESS_KEY"],
        os.environ["MINIO_SECRET_KEY"],
    )
    violations = validate_run(
        s3, cfg.bucket, [t.name for t in cfg.tables], extract_date, run_id
    )
    bad = {table: v for table, v in violations.items() if v}
    if bad:
        raise AirflowException(f"manifest violations: {json.dumps(bad)}")


with DAG(
    dag_id="ingest_oltp_batch",
    default_args=DEFAULT_ARGS,
    schedule=None,
    catchup=False,
    start_date=datetime(2026, 8, 15, tzinfo=timezone.utc),
    description="Extract OLTP tables to MinIO landing with manifests",
) as dag:

    check = PythonOperator(task_id="check_mysql", python_callable=check_mysql)

    begin = PythonOperator(task_id="begin_run", python_callable=begin_run)

    capture = PythonOperator(
        task_id="capture_high_watermarks",
        python_callable=capture_high_watermarks,
    )

    extract = SparkSubmitOperator(
        task_id="extract_tables_to_landing",
        application=SPARK_APP,
        application_args=[
            "--config-path", CONFIG_PATH,
            "--run-id", "{{ ti.xcom_pull(task_ids='begin_run', key='run_id') }}",
            "--extract-date", "{{ ti.xcom_pull(task_ids='begin_run', key='extract_date') }}",
            "--high-watermarks",
            "{{ ti.xcom_pull(task_ids='capture_high_watermarks') | tojson }}",
        ],
    )

    validate = PythonOperator(
        task_id="validate_landing_manifests",
        python_callable=validate_landing_manifests,
    )

    check >> begin >> capture >> extract >> validate
```

- [ ] **Bước 2: Verify DAG parse trong container**

Chạy: `docker compose --profile batch exec airflow-scheduler python -c "from dags.ingest_oltp_batch import dag; print('dag ok', dag.dag_id)"`
Kỳ vọng: `dag ok ingest_oltp_batch` (nếu `dags` không import được như package, chạy `python /opt/airflow/dags/ingest_oltp_batch.py` — phải exit 0).

- [ ] **Bước 3: Trigger DAG thủ công**

```bash
docker compose --profile batch exec airflow-scheduler airflow dags trigger ingest_oltp_batch
docker compose --profile batch exec airflow-scheduler airflow dags list-runs -d ingest_oltp_batch -o table
```

Đợi hoàn tất (poll `airflow tasks list-runs -d ingest_oltp_batch`), rồi xem trạng thái task. Kỳ vọng: cả 5 task `success`.

- [ ] **Bước 4: Verify objects trên Landing (boto3 — airflow image không có aws CLI)**

```bash
docker compose --profile batch exec -T airflow-scheduler python - <<'EOF'
import os
from lakehouse.validate import s3_client
s3 = s3_client(os.environ["MINIO_ENDPOINT"], os.environ["MINIO_ACCESS_KEY"], os.environ["MINIO_SECRET_KEY"])
resp = s3.list_objects_v2(Bucket=os.environ["MINIO_LAKEHOUSE_BUCKET"], Prefix="landing/oltp/")
keys = [o["Key"] for o in resp.get("Contents", [])]
tables = sorted({k.split("/")[2] for k in keys if len(k.split("/")) > 3})
manifests = [k for k in keys if k.endswith("manifest.json")]
print("tables:", len(tables))
print("manifests:", len(manifests))
EOF
```

Kỳ vọng: `tables: 16`, `manifests: 16` (mọi bảng full extract nên đều có parquet + manifest), và `state/cursor/` vẫn chưa tồn tại (commit cursor thuộc Section 5).

- [ ] **Bước 5: Chứng minh hành vi — full re-extract ổn định, delta qua cursor fixture, empty run**

Vì pipeline CHƯA ghi cursor ở Section 3 (§10.3), mọi lần chạy DAG là full extract. Để chứng minh cơ chế incremental, dùng **cursor fixture thủ công** (boto3 `put_object` vào `state/cursor/`, đúng shape `CursorState.from_json`) rồi dọn dẹp sau khi test xong. Bước này gồm 4 thí nghiệm:

```bash
# 1) Lần 2: trigger lại DAG — full re-extract, rows KHÔNG đổi so với lần 1
docker compose --profile batch exec airflow-scheduler airflow dags trigger ingest_oltp_batch
#    (đối chiếu rows qua manifest của lần chạy mới nhất vs lần 1 — phải bằng nhau)

# 2) Chèn 1 order mới (đã validate: status='paid' hợp CHECK + bắt buộc paid_at,
#    cart còn trống qua LEFT JOIN, key unique qua UUID):
docker compose --profile core exec -T mysql-ecommerce sh -c 'export MYSQL_PWD="$MYSQL_PASSWORD"; mysql --protocol=socket -u"$MYSQL_USER" "$MYSQL_DATABASE" -e "
INSERT INTO orders (order_number, cart_id, customer_id, checkout_idempotency_key, status, currency_code, subtotal_vnd, shipping_fee_vnd, total_vnd, receiver_name, receiver_phone, shipping_address_text, data_origin, paid_at, created_at, updated_at)
VALUES (CONCAT('\''MANUAL-'\'', SUBSTRING(REPLACE(UUID(),'\''-'\'','\'''\''),1,24)), (SELECT c.cart_id FROM carts c LEFT JOIN orders o ON o.cart_id=c.cart_id WHERE o.cart_id IS NULL LIMIT 1), 1, UUID(), '\''paid'\'', '\''VND'\'', 10000, 2000, 12000, '\''Test'\'', '\''0900000001'\'', '\''Test addr'\'', '\''manual'\'', NOW(6), NOW(6), NOW(6))"'

# 3) Thí nghiệm delta: viết cursor fixture = high watermark lần chạy 1 (cả 16 bảng),
#    rồi chạy extract trực tiếp; kỳ vọng orders rows=1, 15 bảng còn lại empty=True
FIX_JSON=$(docker compose --profile batch exec -T airflow-scheduler python - <<'EOF'
import json, os
import boto3, pymysql
from sqlalchemy.engine.url import make_url
from lakehouse.config import load_config
cfg = load_config(os.environ["PIPELINE_CONFIG_PATH"])
s3 = boto3.client("s3", endpoint_url=os.environ["MINIO_ENDPOINT"],
                  aws_access_key_id=os.environ["MINIO_ACCESS_KEY"],
                  aws_secret_access_key=os.environ["MINIO_SECRET_KEY"],
                  region_name="us-east-1")
bucket = os.environ["MINIO_LAKEHOUSE_BUCKET"]
url = make_url(os.environ["MYSQL_ECOMMERCE_READER_URL"])
conn = pymysql.connect(host=url.host, port=url.port or 3306,
                       user=url.username, password=url.password, database=url.database)
result = {}
try:
    with conn.cursor() as cur:
        for t in cfg.tables:
            cur.execute(
                f"SELECT MAX(`{t.cursor_field}`) AS at, MAX(`{t.pk}`) AS pk_at_max "
                f"FROM `{t.name}` WHERE `{t.cursor_field}` = "
                f"(SELECT MAX(`{t.cursor_field}`) FROM `{t.name}`)"
            )
            row = cur.fetchone()
            state = {"cursor_at": str(row[0]), "cursor_pk": row[1],
                     "updated_at_utc": "2026-08-15T12:00:00Z"}
            s3.put_object(Bucket=bucket, Key=f"state/cursor/{t.name}.json",
                          Body=json.dumps(state))
            result[t.name] = {"at": str(row[0]), "pk": row[1]}
finally:
    conn.close()
print(json.dumps(result))
EOF
)
docker compose --profile batch exec airflow-scheduler spark-submit \
  /opt/project/pipelines/src/jobs/extract_oltp.py \
  --config-path /opt/project/pipelines/config/default.yml \
  --run-id deltademo --extract-date 2026-08-15 \
  --high-watermarks "$FIX_JSON"

# 4) Thí nghiệm empty: viết lại cursor fixture = MAX(updated_at) hiện tại (không có row mới hơn)
#    rồi chạy lại; kỳ vọng CẢ 16 bảng đều empty=True (dùng lại FIX_JSON vừa chụp —
#    nó là max hiện tại; không cần chạy lại vòng loop)
docker compose --profile batch exec airflow-scheduler spark-submit \
  /opt/project/pipelines/src/jobs/extract_oltp.py \
  --config-path /opt/project/pipelines/config/default.yml \
  --run-id emptydemo --extract-date 2026-08-15 \
  --high-watermarks "$FIX_JSON"

# 5) Dọn dẹp fixture cursor (pipeline không được để lại cursor ở Section 3):
docker compose --profile batch exec -T airflow-scheduler python - <<'EOF'
import os
import boto3
s3 = boto3.client("s3", endpoint_url=os.environ["MINIO_ENDPOINT"],
                  aws_access_key_id=os.environ["MINIO_ACCESS_KEY"],
                  aws_secret_access_key=os.environ["MINIO_SECRET_KEY"],
                  region_name="us-east-1")
bucket = os.environ["MINIO_LAKEHOUSE_BUCKET"]
keys = [o["Key"] for o in s3.list_objects_v2(Bucket=bucket, Prefix="state/cursor/")
        .get("Contents", [])]
for k in keys:
    s3.delete_object(Bucket=bucket, Key=k)
print("deleted:", len(keys))
EOF
```

Kỳ vọng chi tiết:
- Lần 2 (full re-extract): mọi bảng rows bằng đúng lần 1 (manifest mới = manifest cũ về rows).
- `deltademo` (fixture = HW lần 1): chỉ `orders` có `rows=1 empty=False` (order vừa chèn có `updated_at` > HW lần 1); 15 bảng còn lại `empty=True` — chứng minh predicate incremental chỉ lấy đúng dữ liệu mới.
- `emptydemo` (fixture = max hiện tại): cả 16 bảng `empty=True` — chứng minh empty-run path + manifest `empty:true`.
- Sau cleanup: `state/cursor/` trống — pipeline không ghi cursor (Section 5 sẽ làm việc này).

- [ ] **Bước 6: Commit**

```bash
git add airflow/dags/ingest_oltp_batch.py
git commit -m "feat(airflow): add ingest_oltp_batch dag with cursor-aware landing extract"
```

---

### Task 8: Docs + review pass cuối

**Files:**
- Tạo mới: `docs/pipelines/batch/ingest_oltp_to_landing.md` (plan này đóng vai trò bản ghi section)
- Sửa: `docs/project/lakehouse-plan.md` — thay DAG sketch trong §7.1 (khoảng dòng 404-416) bằng danh sách task đã triển khai (`check_mysql, begin_run, capture_high_watermarks, extract_tables_to_landing, validate_landing_manifests, ...Bronze Section 4`) và thêm ghi chú vào §5.2 rằng `state/cursor/` nằm cùng bucket.
- Test: chạy toàn bộ unit suite 1 lần nữa + trigger DAG thủ công 1 lần.

- [ ] **Bước 1: Cập nhật docs**

Áp dụng 2 sửa đổi docs như mô tả trên. Giữ ngắn gọn và thực tế; style tiếng Việt khớp docs hiện có.

- [ ] **Bước 2: Regression toàn bộ**

Chạy: `docker compose --profile batch exec -e PYTHONPATH=/opt/project/pipelines/src airflow-scheduler python -m pytest /opt/project/pipelines/tests -q`
Kỳ vọng: toàn bộ pass — `32 passed` (14 config + 6 cursor + 9 landing + 3 validate).

Chạy: trigger DAG thêm 1 lần nữa; mọi task success.

- [ ] **Bước 3: Commit**

```bash
git add docs/project/lakehouse-plan.md docs/pipelines/batch/ingest_oltp_to_landing.md
git commit -m "docs(pipelines): record section 3 landing extract plan and DAG update"
```

---

## Tiêu chí chấp nhận (trạng thái cuối của Section 3)

1. DAG `ingest_oltp_batch` chạy end-to-end: 5 task, tất cả success.
2. 16 prefix bảng tồn tại dưới `landing/oltp/<table>/extract_date=.../run_id=.../` với `manifest.json` + parquet; mọi lần chạy tạo run dir mới, không sửa/xóa run dir cũ (bất biến).
3. Lần chạy thứ hai (full re-extract) có rows bằng đúng lần chạy thứ nhất; cursor fixture ở high watermark lần 1 → chỉ `orders` rows=1, 15 bảng còn lại empty; cursor fixture ở max hiện tại → cả 16 bảng empty — chứng minh predicate incremental và empty-run path.
4. `validate_landing_manifests` làm DAG fail nếu file manifest thiếu hoặc row count lệch (xác nhận bằng unit tests + thí nghiệm fixture ở Task 7 Bước 5).
5. `state/cursor/` trống sau khi pipeline chạy (fixture đã dọn) — pipeline tự ghi cursor sẽ tới ở Section 5 sau khi Silver publish (spec §10.3).