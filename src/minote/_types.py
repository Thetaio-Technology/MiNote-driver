from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


SECTION_ALL_NOTES = "全部笔记"
SECTION_UNCATEGORIZED = "未分类"
SECTION_RECYCLE_BIN = "最近删除"
SECTION_PENDING = "未完成"
SECTION_COMPLETED = "已完成"

SUPPORTED_SEARCH_SECTIONS = {
    SECTION_ALL_NOTES,
    SECTION_UNCATEGORIZED,
    SECTION_PENDING,
    SECTION_COMPLETED,
}


@dataclass
class TodoItem:
    title: str
    counter: str = ""
    remind: str = ""
    status: str = ""


@runtime_checkable
class MiNoteDriver(Protocol):
    def read_todos(self, section: str) -> list[TodoItem]: ...
    def create_todo(self, title: str, *, section: str = SECTION_PENDING) -> bool: ...
    def update_todo_title(self, old_title: str, new_title: str, *, section: str = SECTION_PENDING) -> bool: ...
    def complete_todo(self, title: str) -> bool: ...
    def restore_todo(self, title: str) -> bool: ...
    def delete_todo(self, title: str, *, section: str = SECTION_PENDING) -> bool: ...
    def search(self, section: str, keyword: str) -> dict: ...
