from pathlib import Path
import argparse
import json
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from minote import (
    COMMAND_COMPLETE,
    COMMAND_CREATE,
    COMMAND_DELETE,
    COMMAND_READ_COMPLETED,
    COMMAND_READ_PENDING,
    COMMAND_RESTORE,
    COMMAND_UPDATE,
    execute_command,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Mi Note todo command runner")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser(COMMAND_READ_PENDING)
    subparsers.add_parser(COMMAND_READ_COMPLETED)

    create_parser = subparsers.add_parser(COMMAND_CREATE)
    create_parser.add_argument("title")

    update_parser = subparsers.add_parser(COMMAND_UPDATE)
    update_parser.add_argument("old_title")
    update_parser.add_argument("new_title")

    complete_parser = subparsers.add_parser(COMMAND_COMPLETE)
    complete_parser.add_argument("title")

    restore_parser = subparsers.add_parser(COMMAND_RESTORE)
    restore_parser.add_argument("title")

    delete_parser = subparsers.add_parser(COMMAND_DELETE)
    delete_parser.add_argument("title")

    return parser


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = build_parser()
    args = parser.parse_args()
    payload = vars(args)
    command = payload.pop("command")
    result = execute_command(command, **payload)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
