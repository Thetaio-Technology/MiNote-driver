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


SKILL_MINOTE_TODO = "minote-todo"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Unified skill runner")
    skill_parsers = parser.add_subparsers(dest="skill", required=True)

    minote_parser = skill_parsers.add_parser(SKILL_MINOTE_TODO, description="MiNote todo skill")
    command_parsers = minote_parser.add_subparsers(dest="command", required=True)

    command_parsers.add_parser(COMMAND_READ_PENDING)
    command_parsers.add_parser(COMMAND_READ_COMPLETED)

    create_parser = command_parsers.add_parser(COMMAND_CREATE)
    create_parser.add_argument("--title", required=True)

    update_parser = command_parsers.add_parser(COMMAND_UPDATE)
    update_parser.add_argument("--old-title", required=True)
    update_parser.add_argument("--new-title", required=True)

    complete_parser = command_parsers.add_parser(COMMAND_COMPLETE)
    complete_parser.add_argument("--title", required=True)

    restore_parser = command_parsers.add_parser(COMMAND_RESTORE)
    restore_parser.add_argument("--title", required=True)

    delete_parser = command_parsers.add_parser(COMMAND_DELETE)
    delete_parser.add_argument("--title", required=True)

    return parser


def execute_skill(skill: str, command: str, payload: dict) -> dict:
    if skill != SKILL_MINOTE_TODO:
        raise ValueError(f"Unsupported skill: {skill}")

    command_args = {
        key: value
        for key, value in payload.items()
        if key not in {"skill", "command"} and value is not None
    }
    result = execute_command(command, **command_args)
    return {
        "skill": skill,
        "result": result,
    }


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = build_parser()
    args = parser.parse_args()
    payload = vars(args)
    skill = payload["skill"]
    command = payload["command"]
    result = execute_skill(skill, command, payload)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
