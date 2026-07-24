import argparse
from pathlib import Path

from tlcn_generator.config import load_config
from tlcn_generator.runner import run


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tlcn-generator")
    subparsers = parser.add_subparsers(dest="command", required=True)
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--config", type=Path, required=True)
    run_parser.add_argument("--output", type=Path, default=Path("/data/generator"))
    return parser


def main() -> None:
    arguments = build_parser().parse_args()
    config = load_config(arguments.config)
    output_path = run(config, arguments.output)
    print(output_path)


if __name__ == "__main__":
    main()

