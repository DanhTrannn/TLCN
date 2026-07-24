import argparse

from tlcn_pipeline.runner import run_stage
from tlcn_pipeline.stages import CORE_STAGES


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tlcn-pipeline")
    parser.add_argument("stage", choices=CORE_STAGES)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--logical-date")
    return parser


def main() -> None:
    arguments = build_parser().parse_args()
    run_stage(arguments.stage, arguments.run_id, arguments.logical_date)


if __name__ == "__main__":
    main()

