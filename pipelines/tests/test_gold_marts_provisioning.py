from pathlib import Path
import yaml


def test_gold_marts_ddl_and_seed_files_exist():
    sql_dir = Path(__file__).resolve().parents[2] / "infrastructure" / "spark" / "sql"
    init_sql = sql_dir / "init_gold_marts.sql"
    seed_sql = sql_dir / "seed_gold_marts.sql"

    assert init_sql.exists(), "init_gold_marts.sql must exist"
    assert seed_sql.exists(), "seed_gold_marts.sql must exist"

    init_content = init_sql.read_text(encoding="utf-8")
    assert "lakehouse.gold.mart_sales_daily" in init_content
    assert "lakehouse.gold.mart_logistics_performance" in init_content
    assert "lakehouse.gold.mart_inventory_health" in init_content
    assert "lakehouse.gold.mart_product_returns" in init_content

    seed_content = seed_sql.read_text(encoding="utf-8")
    assert "INSERT INTO lakehouse.gold.mart_sales_daily" in seed_content
    assert "INSERT INTO lakehouse.gold.mart_logistics_performance" in seed_content
    assert "INSERT INTO lakehouse.gold.mart_inventory_health" in seed_content
