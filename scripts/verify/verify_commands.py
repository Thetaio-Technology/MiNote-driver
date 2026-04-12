from pathlib import Path
import json
import sys
import time

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


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    title = f"cmd-test-{int(time.time())}"
    updated = title + "-updated"

    result = {
        "read_pending_before": execute_command(COMMAND_READ_PENDING),
        "create": execute_command(COMMAND_CREATE, title=title),
        "update": execute_command(COMMAND_UPDATE, old_title=title, new_title=updated),
        "complete": execute_command(COMMAND_COMPLETE, title=updated),
        "read_completed": execute_command(COMMAND_READ_COMPLETED),
        "restore": execute_command(COMMAND_RESTORE, title=updated),
        "delete": execute_command(COMMAND_DELETE, title=updated),
        "read_pending_after": execute_command(COMMAND_READ_PENDING),
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
