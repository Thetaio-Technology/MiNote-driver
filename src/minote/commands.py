from __future__ import annotations

from dataclasses import asdict

from .config import get_driver_mode
from ._types import SECTION_COMPLETED, SECTION_PENDING


COMMAND_READ_PENDING = "read-pending"
COMMAND_READ_COMPLETED = "read-completed"
COMMAND_CREATE = "create"
COMMAND_UPDATE = "update"
COMMAND_COMPLETE = "complete"
COMMAND_RESTORE = "restore"
COMMAND_DELETE = "delete"


def _create_client():
    mode = get_driver_mode()
    if mode == "http":
        from .http_client import MiNoteHttpClient
        return MiNoteHttpClient()
    else:
        from .client import MiNoteClient
        return MiNoteClient(headless=True)


def _dispatch(client, command: str, **kwargs) -> dict:
    if command == COMMAND_READ_PENDING:
        items = [asdict(item) for item in client.read_todos(SECTION_PENDING)]
        return {"command": command, "items": items}

    if command == COMMAND_READ_COMPLETED:
        items = [asdict(item) for item in client.read_todos(SECTION_COMPLETED)]
        return {"command": command, "items": items}

    if command == COMMAND_CREATE:
        title = kwargs["title"]
        ok = client.create_todo(title, section=SECTION_PENDING)
        return {"command": command, "title": title, "ok": ok}

    if command == COMMAND_UPDATE:
        old_title = kwargs["old_title"]
        new_title = kwargs["new_title"]
        ok = client.update_todo_title(old_title, new_title, section=SECTION_PENDING)
        return {"command": command, "old_title": old_title, "new_title": new_title, "ok": ok}

    if command == COMMAND_COMPLETE:
        title = kwargs["title"]
        ok = client.complete_todo(title)
        return {"command": command, "title": title, "ok": ok}

    if command == COMMAND_RESTORE:
        title = kwargs["title"]
        ok = client.restore_todo(title)
        return {"command": command, "title": title, "ok": ok}

    if command == COMMAND_DELETE:
        title = kwargs["title"]
        ok = client.delete_todo(title, section=SECTION_PENDING)
        return {"command": command, "title": title, "ok": ok}

    raise ValueError(f"Unsupported command: {command}")


def execute_command(command: str, **kwargs) -> dict:
    mode = get_driver_mode()
    client = _create_client()

    if mode == "http":
        return _dispatch(client, command, **kwargs)
    else:
        with client:
            return _dispatch(client, command, **kwargs)
