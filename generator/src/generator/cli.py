import argparse
from pathlib import Path

from generator.config import load_config
from generator.runner import run
from generator.sql_export import export_sql


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="generator")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Write the scenario manifest")
    run_parser.add_argument("--config", type=Path, required=True)
    run_parser.add_argument("--output", type=Path, default=Path("/data/generator"))

    sql_parser = subparsers.add_parser("export-sql", help="Generate an importable MySQL dataset")
    sql_parser.add_argument("--config", type=Path, required=True)
    sql_parser.add_argument("--output", type=Path)
    return parser


def main() -> None:
    arguments = build_parser().parse_args()
    config = load_config(arguments.config)

    if arguments.command == "run":
        output_path = run(config, arguments.output)
        print(output_path)
        return

    output_path = arguments.output or Path("/data/generator") / f"{config.scenario_id}-{config.logical_identity}.sql"
    summary = export_sql(config, output_path)
    print(f"SQL file: {summary.sql_path}")
    print(f"Generation run: {summary.generation_run_id}")
    print(f"Rows: {summary.customers} customers, {summary.products} products, {summary.variants} variants, {summary.orders} orders")
    print(f"Demo login: {summary.demo_email} / {summary.demo_password}")


if __name__ == "__main__":
    main()
