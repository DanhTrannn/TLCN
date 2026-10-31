"""Submit the access-log Flink pipeline."""

from lakehouse.logs.streaming import run_access_stream


def main():
    run_access_stream()


if __name__ == "__main__":
    main()
