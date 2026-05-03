from __future__ import annotations

import json
import time

import requests

from .config import CHROME_PROFILE_DIR, MI_API_BASE
from ._cookies import get_cookies
from ._types import (
    SECTION_COMPLETED,
    SECTION_PENDING,
    SUPPORTED_SEARCH_SECTIONS,
    TodoItem,
)


class MiNoteHttpClient:
    def __init__(self) -> None:
        self._session = requests.Session()
        self._records_cache: list[dict] | None = None
        self._sync_token: dict = {}
        self._sort_orders: list[str] = []
        self._sort_etag: str = ""
        self._service_token: str = ""
        self._setup_auth()

    def __enter__(self) -> MiNoteHttpClient:
        return self

    def __exit__(self, *args) -> None:
        pass

    def _setup_auth(self) -> None:
        cookies = get_cookies(CHROME_PROFILE_DIR, domain=".mi.com")
        self._service_token = cookies.get("serviceToken", "")
        if not self._service_token:
            raise RuntimeError(
                "serviceToken not found in Chrome profile cookies. "
                "Run 'python scripts/cli/open_mi_cloud.py' to log in first."
            )
        for name, value in cookies.items():
            if name in ("userId", "i.mi.com_isvalid_servicetoken", "i.mi.com_istrudev"):
                self._session.cookies.set(name, value, domain=".mi.com")
            else:
                self._session.cookies.set(name, value, domain=".i.mi.com")

    def _get(self, path: str, params: dict | None = None) -> dict:
        resp = self._session.get(f"{MI_API_BASE}{path}", params=params)
        resp.raise_for_status()
        result = resp.json()
        if result.get("result") != "ok":
            raise RuntimeError(f"API error: {result.get('description', result)}")
        return result

    def _post(self, path: str, data: dict) -> dict:
        data["serviceToken"] = self._service_token
        resp = self._session.post(
            f"{MI_API_BASE}{path}",
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"},
        )
        resp.raise_for_status()
        result = resp.json()
        if result.get("result") != "ok":
            raise RuntimeError(f"API error: {result.get('description', result)}")
        return result

    def _fetch_all_records(self) -> list[dict]:
        if self._records_cache is not None:
            return self._records_cache

        ts = str(int(time.time() * 1000))
        data = self._get("/todo/v1/user/records", params={"limit": 200, "ts": ts})
        records = data.get("data", {}).get("records", [])
        self._sync_token = data.get("data", {}).get("syncToken", {})

        for rec in records:
            if rec.get("type") == "folder" or str(rec.get("id")) == "0":
                sort_info = rec.get("contentJson", {}).get("sort", {})
                self._sort_orders = sort_info.get("orders", [])
                self._sort_etag = sort_info.get("eTag", "")
                break

        self._records_cache = [r for r in records if r.get("type") == "entity"]
        return self._records_cache

    def _invalidate_cache(self) -> None:
        self._records_cache = None

    def _find_record_by_title(self, title: str, *, completed: bool = False) -> dict | None:
        records = self._fetch_all_records()
        is_finish = 1 if completed else 0
        for rec in records:
            entity = rec.get("contentJson", {}).get("entity", {})
            if entity.get("content", "") == title and entity.get("isFinish", 0) == is_finish:
                return rec
        return None

    def _entity_to_flat_content_json(self, entity: dict) -> dict:
        flat = dict(entity)
        flat["assets"] = []
        return flat

    def _sync_sort(self, orders: list[str]) -> None:
        record = {
            "type": "sort",
            "id": 0,
            "eTag": 0,
            "contentJson": {
                "eTag": self._sort_etag,
                "orders": orders,
            },
        }
        self._post("/todo/v1/user/records/0/update", {
            "previousETag": "0",
            "record": json.dumps(record),
        })

    # ---- Public API ----

    def read_todos(self, section: str) -> list[TodoItem]:
        if section not in {SECTION_PENDING, SECTION_COMPLETED}:
            raise ValueError(f"Todo reading only supports pending/completed, got: {section}")
        records = self._fetch_all_records()
        is_finish = 1 if section == SECTION_COMPLETED else 0
        items = []
        for rec in records:
            entity = rec.get("contentJson", {}).get("entity", {})
            if entity.get("isFinish", 0) == is_finish:
                items.append(TodoItem(
                    title=entity.get("content", ""),
                    status="completed" if is_finish else "pending",
                ))
        return items

    def create_todo(self, title: str, *, section: str = SECTION_PENDING) -> bool:
        now = int(time.time() * 1000)
        record = {
            "type": "entity",
            "contentJson": {
                "listType": 0,
                "content": title,
                "plainText": title,
                "isFinish": 0,
                "markFinishTime": 0,
                "remindType": 0,
                "remindRepeatType": 0,
                "remindTime": 0,
                "firstRemindTime": 0,
                "audioFileField": "",
                "audioFileName": "",
                "audioFileSize": 0,
                "createTime": now,
                "lastModifiedTime": now,
                "inputType": 0,
                "id": 0,
                "customSortId": 0,
                "expireTime": 0,
                "hideType": 0,
                "folderId": 0,
                "colorLabel": 0,
                "source": 0,
                "localStatus": 0,
                "serverStatus": 0,
                "is_finish": False,
                "assets": [],
            },
        }
        result = self._post("/todo/v1/user/records", {
            "record": json.dumps(record),
        })
        created = result.get("data", {}).get("record", {})
        created_id = created.get("id")
        if created_id:
            new_orders = [str(created_id)] + [o for o in self._sort_orders if o != str(created_id)]
            self._sync_sort(new_orders)
        self._invalidate_cache()
        return bool(created_id)

    def update_todo_title(self, old_title: str, new_title: str, *, section: str = SECTION_PENDING) -> bool:
        completed = section == SECTION_COMPLETED
        rec = self._find_record_by_title(old_title, completed=completed)
        if not rec:
            return False

        entity = rec.get("contentJson", {}).get("entity", {})
        flat_cj = self._entity_to_flat_content_json(entity)
        flat_cj["content"] = new_title
        flat_cj["plainText"] = new_title
        flat_cj["lastModifiedTime"] = int(time.time() * 1000)

        record = {
            "id": rec["id"],
            "eTag": rec["eTag"],
            "type": "entity",
            "contentJson": flat_cj,
        }
        self._post(f"/todo/v1/user/records/{rec['id']}/update", {
            "previousETag": str(rec["eTag"]),
            "record": json.dumps(record),
        })
        self._invalidate_cache()
        return True

    def complete_todo(self, title: str) -> bool:
        rec = self._find_record_by_title(title, completed=False)
        if not rec:
            return False

        entity = rec.get("contentJson", {}).get("entity", {})
        flat_cj = self._entity_to_flat_content_json(entity)
        now = int(time.time() * 1000)
        flat_cj["isFinish"] = 1
        flat_cj["markFinishTime"] = now
        flat_cj["lastModifiedTime"] = now

        record = {
            "id": rec["id"],
            "eTag": rec["eTag"],
            "type": "entity",
            "contentJson": flat_cj,
        }
        self._post(f"/todo/v1/user/records/{rec['id']}/update", {
            "previousETag": str(rec["eTag"]),
            "record": json.dumps(record),
        })
        rec_id = str(rec["id"])
        self._sync_sort([o for o in self._sort_orders if o != rec_id])
        self._invalidate_cache()
        return True

    def restore_todo(self, title: str) -> bool:
        rec = self._find_record_by_title(title, completed=True)
        if not rec:
            return False

        entity = rec.get("contentJson", {}).get("entity", {})
        flat_cj = self._entity_to_flat_content_json(entity)
        now = int(time.time() * 1000)
        flat_cj["isFinish"] = 0
        flat_cj["markFinishTime"] = 0
        flat_cj["lastModifiedTime"] = now

        record = {
            "id": rec["id"],
            "eTag": rec["eTag"],
            "type": "entity",
            "contentJson": flat_cj,
        }
        self._post(f"/todo/v1/user/records/{rec['id']}/update", {
            "previousETag": str(rec["eTag"]),
            "record": json.dumps(record),
        })
        rec_id = str(rec["id"])
        self._sync_sort([rec_id] + [o for o in self._sort_orders if o != rec_id])
        self._invalidate_cache()
        return True

    def delete_todo(self, title: str, *, section: str = SECTION_PENDING) -> bool:
        completed = section == SECTION_COMPLETED
        rec = self._find_record_by_title(title, completed=completed)
        if not rec:
            return False

        self._post(f"/todo/v1/user/records/{rec['id']}/delete", {
            "prevETag": str(rec["eTag"]),
        })
        self._invalidate_cache()
        return True

    def search(self, section: str, keyword: str) -> dict:
        if section not in SUPPORTED_SEARCH_SECTIONS:
            raise ValueError(f"Search not supported for section: {section}")
        if section in {SECTION_PENDING, SECTION_COMPLETED}:
            items = self.read_todos(section)
            matched = [item.__dict__ for item in items if keyword.lower() in item.title.lower()]
        else:
            matched = []
        return {
            "section": section,
            "keyword": keyword,
            "items": matched,
        }
