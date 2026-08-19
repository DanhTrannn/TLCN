import argparse
from pathlib import Path

from generator.config import load_config
from generator.log_export import export_logs
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

    logs_parser = subparsers.add_parser(
        "export-logs",
        help="Generate deterministic 15-minute access-log Landing files",
    )
    logs_parser.add_argument("--config", type=Path, required=True)
    logs_parser.add_argument(
        "--output-directory",
        type=Path,
        default=Path("/data/generator/access-logs"),
    )
    logs_parser.add_argument(
        "--expected-requests",
        type=int,
        help="Expected total; defaults to 20 access requests per configured order",
    )
    return parser


def main() -> None:
    arguments = build_parser().parse_args()
    config = load_config(arguments.config)

    if arguments.command == "run":
        output_path = run(config, arguments.output)
        print(output_path)
        return

    if arguments.command == "export-logs":
        expected_requests = arguments.expected_requests or max(
            1_000,
            config.scale.get("orders", 0) * 20,
        )
        summary = export_logs(
            config,
            arguments.output_directory,
            expected_requests=expected_requests,
        )
        print(f"Landing root: {summary.output_root}")
        print(f"Log logical identity: {summary.logical_identity}")
        print(
            f"Requests: {summary.emitted_requests} emitted "
            f"({summary.expected_requests} expected)"
        )
        print(f"Files: {summary.files} .jsonl.gz")
        return

    output_path = arguments.output or Path("/data/generator") / f"{config.scenario_id}-{config.logical_identity}.sql"
    summary = export_sql(config, output_path)
    print(f"SQL file: {summary.sql_path}")
    print(f"Generation run: {summary.generation_run_id}")
    print(f"Rows: {summary.customers} customers, {summary.products} products, {summary.variants} variants, {summary.orders} orders")
    print(f"Demo login: {summary.demo_email} / {summary.demo_password}")


if __name__ == "__main__":
    main()
