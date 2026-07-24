import argparse

from repurchase_ml.runner import run_stage
from repurchase_ml.stages import ML_STAGES


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tlcn-repurchase-ml")
    parser.add_argument("stage", choices=ML_STAGES)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--logical-date")
    return parser


def main() -> None:
    arguments = build_parser().parse_args()
    run_stage(arguments.stage, arguments.run_id, arguments.logical_date)


if __name__ == "__main__":
    main()

