# Mi Note API

## Overview

This project automates Xiaomi Cloud Notes todo operations through a locally logged-in Chrome profile.

Current scope:

- Read pending todos
- Read completed todos
- Create todos
- Update todo titles
- Complete todos
- Restore completed todos back to pending
- Delete todos

Out of scope for now:

- Private notes (`私密笔记`)
- Private-note search
- Private-note read

## Runtime Requirements

- Windows
- Google Chrome installed at `C:\Program Files\Google\Chrome\Application\chrome.exe`
- Matching `chromedriver.exe` at `bin/chromedriver.exe`
- Logged-in Chrome profile stored in `chrome_profile/`
- Python with `selenium` installed

The automation uses the local Chrome profile in this project directory, not the system default browser profile.

## Main Files

- `src/minote/client.py`: browser automation client
- `src/minote/commands.py`: command executor
- `src/minote/browser.py`: browser launcher helpers
- `scripts/cli/mi_note_commands.py`: CLI entrypoint
- `scripts/verify/verify_todo_crud.py`: CRUD verification against the live site
- `scripts/verify/verify_commands.py`: command-layer verification against the live site
- `scripts/cli/open_mi_cloud.py`: opens the Xiaomi Notes page with the local Chrome profile
- `scripts/debug/`: inspection and one-off debugging scripts

## Client API

Main class:

```python
from minote import MiNoteClient
```

Use it as a context manager:

```python
from minote import MiNoteClient, SECTION_PENDING

with MiNoteClient(headless=True) as client:
    items = client.read_todos(SECTION_PENDING)
```

### Section Constants

Available constants:

- `SECTION_ALL_NOTES = "全部笔记"`
- `SECTION_UNCATEGORIZED = "未分类"`
- `SECTION_RECYCLE_BIN = "最近删除"`
- `SECTION_PENDING = "未完成"`
- `SECTION_COMPLETED = "已完成"`

### Data Model

Todo items are returned as `TodoItem` objects:

```python
@dataclass
class TodoItem:
    title: str
    counter: str = ""
    remind: str = ""
    status: str = ""
```

### Methods

#### `list_sidebar_items() -> list[str]`

Returns visible sidebar entries.

Example result:

```json
[
  "全部笔记",
  "未分类",
  "我的文件夹",
  "私密笔记",
  "最近删除",
  "未完成",
  "已完成"
]
```

#### `open_section(section: str) -> None`

Switches to a sidebar section.

#### `read_todos(section: str) -> list[TodoItem]`

Supported sections:

- `SECTION_PENDING`
- `SECTION_COMPLETED`

Example:

```python
items = client.read_todos(SECTION_PENDING)
for item in items:
    print(item.title)
```

#### `create_todo(title: str, section: str = SECTION_PENDING) -> bool`

Creates a todo in the target todo section.

Current usage is intended for `SECTION_PENDING`.

Example:

```python
ok = client.create_todo("明天下午买咖啡豆")
```

#### `update_todo_title(old_title: str, new_title: str, section: str = SECTION_PENDING) -> bool`

Updates a todo title in the target section.

Example:

```python
ok = client.update_todo_title("买棉签", "买棉签和牙线")
```

#### `complete_todo(title: str) -> bool`

Moves a todo from `未完成` to `已完成`.

Example:

```python
ok = client.complete_todo("洗衣服")
```

#### `restore_todo(title: str) -> bool`

Moves a todo from `已完成` back to `未完成`.

Example:

```python
ok = client.restore_todo("洗车")
```

#### `delete_todo(title: str, section: str = SECTION_PENDING) -> bool`

Deletes a todo permanently.

Actual UI path used by automation:

1. Right-click todo item
2. Click `删除`
3. Confirm modal dialog by clicking `删除`

Example:

```python
ok = client.delete_todo("剪头发")
```

#### `get_search_placeholder() -> str | None`

Returns the visible search input placeholder for the current page, if present.

#### `search(section: str, keyword: str) -> dict`

Search support currently exists for these sections:

- `全部笔记`
- `未分类`
- `未完成`
- `已完成`

Notes:

- Search input presence is verified
- Search result behavior is less stable than todo CRUD and should be treated as provisional

## Command API

Import from:

```python
from minote import execute_command
```

### Command Constants

- `COMMAND_READ_PENDING = "read-pending"`
- `COMMAND_READ_COMPLETED = "read-completed"`
- `COMMAND_CREATE = "create"`
- `COMMAND_UPDATE = "update"`
- `COMMAND_COMPLETE = "complete"`
- `COMMAND_RESTORE = "restore"`
- `COMMAND_DELETE = "delete"`

### `execute_command(command: str, **kwargs) -> dict`

Supported calls:

#### Read pending todos

```python
execute_command("read-pending")
```

#### Read completed todos

```python
execute_command("read-completed")
```

#### Create todo

```python
execute_command("create", title="明天下午买咖啡豆")
```

#### Update todo

```python
execute_command("update", old_title="买棉签", new_title="买棉签和牙线")
```

#### Complete todo

```python
execute_command("complete", title="洗衣服")
```

#### Restore todo

```python
execute_command("restore", title="洗车")
```

#### Delete todo

```python
execute_command("delete", title="剪头发")
```

## CLI Usage

### Read pending

```bash
python scripts/cli/mi_note_commands.py read-pending
```

### Read completed

```bash
python scripts/cli/mi_note_commands.py read-completed
```

### Create

```bash
python scripts/cli/mi_note_commands.py create "明天下午买咖啡豆"
```

### Update

```bash
python scripts/cli/mi_note_commands.py update "旧标题" "新标题"
```

### Complete

```bash
python scripts/cli/mi_note_commands.py complete "洗衣服"
```

### Restore

```bash
python scripts/cli/mi_note_commands.py restore "洗车"
```

### Delete

```bash
python scripts/cli/mi_note_commands.py delete "剪头发"
```

## Verification

### Client-layer CRUD verification

```bash
python scripts/verify/verify_todo_crud.py
```

This verifies:

- create
- update
- complete
- restore
- delete

### Command-layer verification

```bash
python scripts/verify/verify_commands.py
```

This verifies command dispatch over the same live browser automation path.

## Known Limits

- The implementation depends on the current Xiaomi Notes web DOM structure
- Private notes are intentionally unsupported
- Search support is not as fully verified as todo CRUD
- The project assumes a working logged-in local Chrome profile in `chrome_profile/`
