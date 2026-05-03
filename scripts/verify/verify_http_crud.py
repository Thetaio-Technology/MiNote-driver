"""Verify HTTP client with full CRUD cycle against live API."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from minote import MiNoteHttpClient, SECTION_COMPLETED, SECTION_PENDING

TEST_TITLE = "__HTTP_VERIFY__"
TEST_UPDATED = "__HTTP_UPDATED__"


def main():
    client = MiNoteHttpClient()
    results = []

    # 1. Read pending (initial state)
    print("=== 1. READ PENDING (before) ===")
    items = client.read_todos(SECTION_PENDING)
    print(f"  {len(items)} pending todos")
    results.append(("read_pending_before", True))

    # 2. Create
    print("\n=== 2. CREATE ===")
    ok = client.create_todo(TEST_TITLE, section=SECTION_PENDING)
    print(f"  create '{TEST_TITLE}': {ok}")
    results.append(("create", ok))

    # 3. Read pending (after create)
    print("\n=== 3. READ PENDING (after create) ===")
    items = client.read_todos(SECTION_PENDING)
    titles = [i.title for i in items]
    found = TEST_TITLE in titles
    print(f"  {len(items)} todos, '{TEST_TITLE}' found: {found}")
    results.append(("read_after_create", found))

    # 4. Update title
    print("\n=== 4. UPDATE TITLE ===")
    ok = client.update_todo_title(TEST_TITLE, TEST_UPDATED, section=SECTION_PENDING)
    print(f"  update to '{TEST_UPDATED}': {ok}")
    results.append(("update", ok))

    # Verify
    items = client.read_todos(SECTION_PENDING)
    titles = [i.title for i in items]
    updated_found = TEST_UPDATED in titles
    print(f"  '{TEST_UPDATED}' found: {updated_found}")
    results.append(("verify_update", updated_found))

    # 5. Complete
    print("\n=== 5. COMPLETE ===")
    ok = client.complete_todo(TEST_UPDATED)
    print(f"  complete: {ok}")
    results.append(("complete", ok))

    # Verify: not in pending
    items = client.read_todos(SECTION_PENDING)
    pending_titles = [i.title for i in items]
    not_in_pending = TEST_UPDATED not in pending_titles
    print(f"  not in pending: {not_in_pending}")

    # Verify: in completed
    items = client.read_todos(SECTION_COMPLETED)
    completed_titles = [i.title for i in items]
    in_completed = TEST_UPDATED in completed_titles
    print(f"  in completed: {in_completed}")
    results.append(("verify_complete", not_in_pending and in_completed))

    # 6. Restore
    print("\n=== 6. RESTORE ===")
    ok = client.restore_todo(TEST_UPDATED)
    print(f"  restore: {ok}")
    results.append(("restore", ok))

    # Verify: back in pending
    items = client.read_todos(SECTION_PENDING)
    titles = [i.title for i in items]
    back_in_pending = TEST_UPDATED in titles
    print(f"  back in pending: {back_in_pending}")
    results.append(("verify_restore", back_in_pending))

    # 7. Delete
    print("\n=== 7. DELETE ===")
    ok = client.delete_todo(TEST_UPDATED, section=SECTION_PENDING)
    print(f"  delete: {ok}")
    results.append(("delete", ok))

    # Verify: gone
    items = client.read_todos(SECTION_PENDING)
    titles = [i.title for i in items]
    gone = TEST_UPDATED not in titles
    print(f"  gone from pending: {gone}")
    results.append(("verify_delete", gone))

    # Summary
    print("\n" + "=" * 50)
    all_ok = all(ok for _, ok in results)
    print(f"RESULT: {'ALL PASSED' if all_ok else 'SOME FAILED'}")
    for name, ok in results:
        print(f"  {name}: {'PASS' if ok else 'FAIL'}")
    print("=" * 50)

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
