import json
import sys

from mi_note_client import (
    MiNoteClient,
    SECTION_ALL_NOTES,
    SECTION_COMPLETED,
    SECTION_PENDING,
    SECTION_UNCATEGORIZED,
)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    with MiNoteClient(headless=True) as client:
        result = {
            "sidebar_items": client.list_sidebar_items(),
            "pending_titles": [item.title for item in client.read_todos(SECTION_PENDING)],
            "completed_titles": [item.title for item in client.read_todos(SECTION_COMPLETED)],
            "pending_search": client.search(SECTION_PENDING, "咖啡"),
            "all_notes_search": client.search(SECTION_ALL_NOTES, "rss"),
            "uncategorized_search": client.search(SECTION_UNCATEGORIZED, "rss"),
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
