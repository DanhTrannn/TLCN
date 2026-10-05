"""Airflow DAG Integrity and Structure Unit Tests.

Validates all DAGs in airflow/dags/:
1. Syntax & Compilation: Verifies all DAG files compile cleanly without syntax errors.
2. AST Static Analysis: Verifies DAG parameters (dag_id, schedule, default_args).
3. Structural Integrity: Validates unique task IDs, absence of cycles (DAG topological sort),
   and expected TaskGroups across Lakehouse batch and streaming pipelines.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

DAG_DIR = Path(__file__).resolve().parents[2] / "airflow" / "dags"


def get_dag_files() -> list[Path]:
    """Retrieve all Python DAG files from airflow/dags."""
    files = list(DAG_DIR.glob("*.py"))
    assert len(files) >= 2, f"Expected at least 2 DAG files in {DAG_DIR}, found {len(files)}"
    return files


def test_dag_files_exist():
    """Verify DAG directory exists and contains expected DAGs."""
    assert DAG_DIR.is_dir(), f"DAG directory {DAG_DIR} does not exist"
    dag_files = [f.name for f in get_dag_files()]
    assert "lakehouse_oltp_pipeline.py" in dag_files
    assert "lakehouse_streaming_maintenance.py" in dag_files
    assert "lakehouse_oltp_maintenance.py" in dag_files


@pytest.mark.parametrize("dag_path", get_dag_files(), ids=lambda p: p.name)
def test_dag_syntax_and_compilation(dag_path: Path):
    """Ensure each DAG file is syntactically valid Python."""
    code = dag_path.read_text(encoding="utf-8")
    # Verify AST can parse without SyntaxError
    parsed_ast = ast.parse(code, filename=str(dag_path))
    assert parsed_ast is not None

    # Verify code can be compiled to bytecode
    compiled = compile(code, str(dag_path), "exec")
    assert compiled is not None


@pytest.mark.parametrize("dag_path", get_dag_files(), ids=lambda p: p.name)
def test_dag_ast_properties(dag_path: Path):
    """Static AST check for DAG instantiation, dag_id and standard arguments."""
    code = dag_path.read_text(encoding="utf-8")
    tree = ast.parse(code, filename=str(dag_path))

    dag_id_found = False
    schedule_found = False

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            # Check if calling DAG(...)
            is_dag_call = False
            if isinstance(node.func, ast.Name) and node.func.id == "DAG":
                is_dag_call = True
            elif isinstance(node.func, ast.Attribute) and node.func.attr == "DAG":
                is_dag_call = True

            if is_dag_call:
                for kw in node.keywords:
                    if kw.arg == "dag_id" and isinstance(kw.value, ast.Constant):
                        dag_id_found = True
                    if kw.arg in ("schedule", "schedule_interval"):
                        schedule_found = True

    assert dag_id_found, f"{dag_path.name} must instantiate a DAG with explicit 'dag_id'"
    assert schedule_found, f"{dag_path.name} must define 'schedule' or 'schedule_interval'"


class MockTask:
    """Mock Airflow Operator representing a task node."""

    def __init__(self, task_id: str, dag: MockDAG | None = None, **kwargs):
        self.task_id = task_id
        self.dag = dag
        self.upstream: set[MockTask] = set()
        self.downstream: set[MockTask] = set()
        if dag is not None:
            dag.add_task(self)

    def __rshift__(self, other):
        """Implement >> operator for chaining."""
        if isinstance(other, MockTask):
            self.downstream.add(other)
            other.upstream.add(self)
        elif isinstance(other, (list, tuple, set)):
            for item in other:
                self.__rshift__(item)
        elif isinstance(other, MockTaskGroup):
            for t in other.get_entry_tasks():
                self.__rshift__(t)
        return other

    def __lshift__(self, other):
        if isinstance(other, MockTask):
            other.__rshift__(self)
        elif isinstance(other, (list, tuple, set)):
            for item in other:
                item.__rshift__(self)
        elif isinstance(other, MockTaskGroup):
            for t in other.get_exit_tasks():
                t.__rshift__(self)
        return other

    def __rrshift__(self, other):
        if isinstance(other, (list, tuple, set)):
            for item in other:
                item.__rshift__(self)
        return self

    def __rlshift__(self, other):
        if isinstance(other, (list, tuple, set)):
            for item in other:
                item.__lshift__(self)
        return self


class MockTaskGroup:
    """Mock Airflow TaskGroup."""

    def __init__(self, group_id: str, dag: MockDAG | None = None, **kwargs):
        self.group_id = group_id
        self.dag = dag
        self.tasks: list[MockTask] = []
        if dag is not None:
            dag.current_group = self

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.dag is not None:
            self.dag.current_group = None

    def add_task(self, task: MockTask):
        self.tasks.append(task)

    def get_entry_tasks(self) -> list[MockTask]:
        return [t for t in self.tasks if not any(up in self.tasks for up in t.upstream)] or self.tasks

    def get_exit_tasks(self) -> list[MockTask]:
        return [t for t in self.tasks if not any(down in self.tasks for down in t.downstream)] or self.tasks

    def __rshift__(self, other):
        for t in self.get_exit_tasks():
            t.__rshift__(other)
        return other

    def __lshift__(self, other):
        for t in self.get_entry_tasks():
            t.__lshift__(other)
        return other

    def __rrshift__(self, other):
        for t in self.get_entry_tasks():
            t.__rrshift__(other)
        return self

    def __rlshift__(self, other):
        for t in self.get_exit_tasks():
            t.__rlshift__(other)
        return self


class MockDAG:
    """Mock Airflow DAG with cycle detection and integrity assertions."""

    def __init__(self, dag_id: str, schedule: str | None = None, schedule_interval: str | None = None, **kwargs):
        self.dag_id = dag_id
        self.schedule = schedule or schedule_interval
        self.default_args = kwargs.get("default_args", {})
        self.tasks: dict[str, MockTask] = {}
        self.task_groups: dict[str, MockTaskGroup] = {}
        self.current_group: MockTaskGroup | None = None

    def __enter__(self):
        MockDAG._active_dag = self
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        MockDAG._active_dag = None

    _active_dag: MockDAG | None = None

    def add_task(self, task: MockTask):
        assert task.task_id not in self.tasks, f"Duplicate task_id '{task.task_id}' found in DAG '{self.dag_id}'"
        self.tasks[task.task_id] = task
        if self.current_group is not None:
            self.current_group.add_task(task)

    def validate_no_cycles(self):
        """Topological sort check to guarantee the task graph is acyclic (DAG)."""
        visited: dict[str, int] = {}  # 0: unvisited, 1: visiting, 2: visited

        def visit(task_id: str, path: list[str]):
            state = visited.get(task_id, 0)
            if state == 1:
                cycle_str = " -> ".join(path + [task_id])
                raise ValueError(f"Cycle detected in DAG '{self.dag_id}': {cycle_str}")
            if state == 2:
                return

            visited[task_id] = 1
            task = self.tasks[task_id]
            for child in task.downstream:
                visit(child.task_id, path + [task_id])
            visited[task_id] = 2

        for tid in self.tasks:
            if visited.get(tid, 0) == 0:
                visit(tid, [])


def _load_dag_with_mocks(dag_path: Path) -> MockDAG:
    """Load and execute a DAG file inside an isolated execution scope with mock Airflow."""
    # Prepare mock modules
    mock_airflow = MagicMock()
    mock_airflow.DAG = MockDAG
    mock_airflow.exceptions.AirflowException = Exception

    mock_python_op = MagicMock()
    mock_python_op.PythonOperator = lambda task_id, **kwargs: MockTask(task_id, dag=MockDAG._active_dag, **kwargs)

    mock_spark_op = MagicMock()
    mock_spark_op.SparkSubmitOperator = lambda task_id, **kwargs: MockTask(task_id, dag=MockDAG._active_dag, **kwargs)

    def make_task_group(group_id, **kwargs):
        tg = MockTaskGroup(group_id, dag=MockDAG._active_dag, **kwargs)
        if MockDAG._active_dag:
            MockDAG._active_dag.task_groups[group_id] = tg
        return tg

    mock_tg_module = MagicMock()
    mock_tg_module.TaskGroup = make_task_group

    captured_dags: list[MockDAG] = []

    def mock_dag_init(*args, **kwargs):
        dag = MockDAG(*args, **kwargs)
        captured_dags.append(dag)
        return dag

    mock_airflow.DAG = mock_dag_init

    mock_pendulum = MagicMock()
    mock_pendulum.timezone = lambda tz: tz
    mock_pendulum.datetime = lambda *a, **kw: MagicMock()
    mock_pendulum.now = lambda *a, **kw: MagicMock(strftime=lambda fmt: "2026-10-01")

    mock_requests = MagicMock()

    mock_sqlalchemy = MagicMock()
    mock_sqlalchemy.engine.url.make_url = lambda url: MagicMock()

    scope = {
        "__file__": str(dag_path),
        "__name__": f"airflow.dags.{dag_path.stem}",
    }

    modules_to_patch = {
        "pendulum": mock_pendulum,
        "requests": mock_requests,
        "sqlalchemy": mock_sqlalchemy,
        "sqlalchemy.engine": mock_sqlalchemy.engine,
        "sqlalchemy.engine.url": mock_sqlalchemy.engine.url,
        "airflow": mock_airflow,
        "airflow.DAG": mock_dag_init,
        "airflow.exceptions": mock_airflow.exceptions,
        "airflow.operators": MagicMock(),
        "airflow.operators.python": mock_python_op,
        "airflow.providers": MagicMock(),
        "airflow.providers.apache": MagicMock(),
        "airflow.providers.apache.spark": MagicMock(),
        "airflow.providers.apache.spark.operators": MagicMock(),
        "airflow.providers.apache.spark.operators.spark_submit": mock_spark_op,
        "airflow.utils": MagicMock(),
        "airflow.utils.task_group": mock_tg_module,
    }

    with patch.dict(sys.modules, modules_to_patch):
        code = dag_path.read_text(encoding="utf-8")
        exec(compile(code, str(dag_path), "exec"), scope)

    assert len(captured_dags) >= 1, f"No DAG was instantiated in {dag_path.name}"
    return captured_dags[0]


def test_oltp_pipeline_structural_integrity():
    """Verify lakehouse_oltp_pipeline DAG structure, task groups, and cycle prevention."""
    dag_path = DAG_DIR / "lakehouse_oltp_pipeline.py"
    dag = _load_dag_with_mocks(dag_path)

    assert dag.dag_id == "lakehouse_oltp_pipeline"
    assert dag.schedule == "0 2 * * *"  # Daily at 2 AM
    assert dag.default_args.get("owner") == "lakehouse"

    # Verify no cyclic dependencies exist
    dag.validate_no_cycles()

    # Verify essential task groups exist
    expected_groups = {"landing_zone", "bronze_layer", "silver_layer", "gold_layer"}
    for group in expected_groups:
        assert group in dag.task_groups, f"Expected task group '{group}' missing from {dag.dag_id}"

    # Verify key tasks exist
    assert "begin_run" in dag.tasks
    assert "check_mysql" in dag.tasks
    assert "capture_high_watermarks" in dag.tasks
    assert "extract_tables_to_landing" in dag.tasks
    assert "validate_landing_manifests" in dag.tasks
    assert "commit_cursors" in dag.tasks
    assert "ingest_oltp_to_bronze" in dag.tasks
    assert "spark_oltp_bronze_to_silver" in dag.tasks
    assert "reconciliation_gate" in dag.tasks
    assert "spark_build_gold_dimensions" in dag.tasks
    assert "spark_build_gold_facts" in dag.tasks
    assert "spark_build_gold_marts" in dag.tasks


def test_oltp_maintenance_structural_integrity():
    """Verify lakehouse_oltp_maintenance DAG structure, task groups, and cycle prevention."""
    dag_path = DAG_DIR / "lakehouse_oltp_maintenance.py"
    dag = _load_dag_with_mocks(dag_path)

    assert dag.dag_id == "lakehouse_oltp_maintenance"
    assert dag.schedule == "0 3 * * *"  # Daily at 3 AM
    assert dag.default_args.get("owner") == "lakehouse"

    # Verify no cyclic dependencies exist
    dag.validate_no_cycles()

    # Verify essential task groups exist
    assert "iceberg_maintenance" in dag.task_groups

    # Verify key maintenance tasks exist
    assert "begin_run" in dag.tasks
    assert "compact_oltp_tables" in dag.tasks
    assert "expire_oltp_snapshots" in dag.tasks
    assert "remove_oltp_orphan_files" in dag.tasks



def test_streaming_maintenance_structural_integrity():
    """Verify lakehouse_streaming_maintenance DAG structure and cycle prevention."""
    dag_path = DAG_DIR / "lakehouse_streaming_maintenance.py"
    dag = _load_dag_with_mocks(dag_path)

    assert dag.dag_id == "lakehouse_streaming_maintenance"
    assert dag.schedule == "0 */2 * * *"  # Every 2 hours
    assert dag.default_args.get("owner") == "lakehouse"

    # Verify no cyclic dependencies exist
    dag.validate_no_cycles()

    # Verify essential task groups exist
    expected_groups = {"stream_monitoring", "iceberg_maintenance", "gold_marts"}
    for group in expected_groups:
        assert group in dag.task_groups, f"Expected task group '{group}' missing from {dag.dag_id}"

    # Verify key maintenance tasks exist
    assert "begin_run" in dag.tasks
    assert "check_flink_streaming_health" in dag.tasks
    assert "compact_iceberg_tables" in dag.tasks
    assert "expire_iceberg_snapshots" in dag.tasks
    assert "remove_orphan_files" in dag.tasks
    assert "rollup_logs_gold_marts" in dag.tasks
