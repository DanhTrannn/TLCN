import ast
from pathlib import Path


def _load_streaming_table_ddls():
    source = Path(__file__).parents[1] / "src" / "lakehouse" / "flink.py"
    tree = ast.parse(source.read_text())
    for node in tree.body:
        if isinstance(node, ast.Assign):
            if any(
                isinstance(target, ast.Name)
                and target.id == "STREAMING_TABLE_DDLS"
                for target in node.targets
            ):
                return ast.literal_eval(node.value)
    raise AssertionError("STREAMING_TABLE_DDLS is not defined")


STREAMING_TABLE_DDLS = _load_streaming_table_ddls()


def test_streaming_profile_provisions_all_sink_tables():
    ddl = "\n".join(STREAMING_TABLE_DDLS)

    assert len(STREAMING_TABLE_DDLS) == 4
    assert "lakehouse.landing.access_logs" in ddl
    assert "lakehouse.bronze.web_events" in ddl
    assert "lakehouse.silver.silver_logs" in ddl
    assert "lakehouse.gold.fact_web_events" in ddl


def test_upsert_sinks_define_primary_keys():
    ddl = "\n".join(STREAMING_TABLE_DDLS[2:])

    assert ddl.count("PRIMARY KEY (event_id) NOT ENFORCED") == 2
    assert ddl.count("'write.upsert.enabled' = 'true'") == 2
