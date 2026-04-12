from pathlib import Path
import json
import sys
import time

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from minote import MiNoteClient, SECTION_COMPLETED, SECTION_PENDING


TEST_TITLE = f"crud-test-{int(time.time())}"
UPDATED_TITLE = TEST_TITLE + "-updated"


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    result = {}
    with MiNoteClient(headless=True) as client:
        result["create"] = client.create_todo(TEST_TITLE, section=SECTION_PENDING)
        result["update"] = client.update_todo_title(TEST_TITLE, UPDATED_TITLE, section=SECTION_PENDING)
        result["complete"] = client.complete_todo(UPDATED_TITLE)
        result["restore"] = client.restore_todo(UPDATED_TITLE)
        result["delete"] = client.delete_todo(UPDATED_TITLE, section=SECTION_PENDING)
        result["pending_titles"] = [item.title for item in client.read_todos(SECTION_PENDING)]
        result["completed_titles"] = [item.title for item in client.read_todos(SECTION_COMPLETED)]

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
