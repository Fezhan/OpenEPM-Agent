import argparse
from openepm_agent.runner import run_loop, ensure_registered


def main():
    parser = argparse.ArgumentParser(
        prog="openepm-agent",
        description="OpenEPM Agent - Lightweight endpoint management agent",
    )
    parser.add_argument(
        "command",
        choices=["start", "enroll"],
        help="Command to run",
    )
    args = parser.parse_args()

    if args.command == "start":
        run_loop()
    elif args.command == "enroll":
        result = ensure_registered()
        print(result)


if __name__ == "__main__":
    main()