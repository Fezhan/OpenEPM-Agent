import argparse
from openepm_agent.runner import run_loop
from openepm_agent.api import register_agent as register


def main():
    parser = argparse.ArgumentParser(
        prog="openepm-agent",
        description="OpenEPM Agent - Lightweight endpoint management agent",
    )
    parser.add_argument(
        "command",
        choices=["start"],
        help="Command to run",
    )
    args = parser.parse_args()

    if args.command == "start":
        run_loop()
    elif args.command == "enroll":
        register()


if __name__ == "__main__":
    main()
