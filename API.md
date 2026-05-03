# Mi Note API

## Overview

This project automates Xiaomi Cloud Notes todo operations through two driver modes:

- **HTTP mode (default)**: Direct REST API calls, no browser required
- **Selenium mode (legacy)**: Browser DOM automation

Both modes expose the same Python API and CLI interface. Configuration is in `minote.toml`.

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

### HTTP mode (default)

- Windows
- Python 3.11+
- `requests`, `pycryptodome`, `pywin32`
- Logged-in Chrome profile stored in `chrome_profile/` (only needed for initial login)
- Chrome does not need to be running

### Selenium mode

- Windows
- Google Chrome installed at `C:\Program Files\Google\Chrome\Application\chrome.exe`
- Matching `chromedriver.exe` at `bin/chromedriver.exe`
- Logged-in Chrome profile stored in `chrome_profile/`
- Python with `selenium` installed

### Configuration

Create or edit `minote.toml` in the project root:

```toml
[driver]
mode = "http"    # "http" (default) or "selenium"
```

## Main Files

- `src/minote/_types.py`: shared Protocol interface, data models, constants
- `src/minote/_cookies.py`: Chrome cookie extraction from disk
- `src/minote/http_client.py`: HTTP REST API client
- `src/minote/client.py`: Selenium browser automation client
- `src/minote/commands.py`: mode-agnostic command executor
- `src/minote/config.py`: path constants, TOML config loading
- `minote.toml`: driver mode configuration
- `scripts/cli/mi_note_commands.py`: CLI entrypoint
- `scripts/cli/run_skill.py`: unified skill entrypoint
- `scripts/cli/open_mi_cloud.py`: opens Xiaomi Notes page for initial login
- `scripts/verify/verify_http_crud.py`: HTTP CRUD verification
- `scripts/verify/verify_todo_crud.py`: Selenium CRUD verification
- `scripts/verify/verify_commands.py`: command-layer verification
- `docs/mi-note-api.md`: reverse-engineered API documentation
- `scripts/debug/`: inspection and one-off debugging scripts

## Client API

### HTTP Client (recommended)

```python
from minote import MiNoteHttpClient, SECTION_PENDING

client = MiNoteHttpClient()
items = client.read_todos(SECTION_PENDING)
for item in items:
    print(item.title)
```

### Selenium Client

```python
from minote import MiNoteClient, SECTION_PENDING

with MiNoteClient(headless=True) as client:
    items = client.read_todos(SECTION_PENDING)
```

Both clients implement the same `MiNoteDriver` Protocol:

```python
class MiNoteDriver(Protocol):
    def read_todos(self, section: str) -> list[TodoItem]: ...
    def create_todo(self, title: str, *, section: str) -> bool: ...
    def update_todo_title(self, old_title: str, new_title: str, *, section: str) -> bool: ...
    def complete_todo(self, title: str) -> bool: ...
    def restore_todo(self, title: str) -> bool: ...
    def delete_todo(self, title: str, *, section: str) -> bool: ...
    def search(self, section: str, keyword: str) -> dict: ...
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

Creates a todo in the target section.

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

Moves a todo from pending to completed.

Example:

```python
ok = client.complete_todo("洗衣服")
```

#### `restore_todo(title: str) -> bool`

Moves a todo from completed back to pending.

Example:

```python
ok = client.restore_todo("洗车")
```

#### `delete_todo(title: str, section: str = SECTION_PENDING) -> bool`

Deletes a todo permanently.

Example:

```python
ok = client.delete_todo("剪头发")
```

#### `search(section: str, keyword: str) -> dict`

Search within a section by keyword (client-side text filtering).

Supported sections:

- `全部笔记`, `未分类`, `未完成`, `已完成`

Example:

```python
result = client.search(SECTION_PENDING, "咖啡")
```

### Selenium-only Methods

The following methods are only available on `MiNoteClient` (Selenium mode):

- `list_sidebar_items() -> list[str]` — returns visible sidebar entries
- `open_section(section: str) -> None` — switches to a sidebar section
- `get_search_placeholder() -> str | None` — returns search input placeholder

## Command API

Import from:

```python
from minote import execute_command
```

`execute_command` automatically selects the driver mode from `minote.toml`.

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

### HTTP CRUD verification

```bash
python scripts/verify/verify_http_crud.py
```

This verifies the full CRUD cycle via REST API: create, read, update, complete, restore, delete.

### Client-layer CRUD verification (Selenium)

```bash
python scripts/verify/verify_todo_crud.py
```

### Command-layer verification

```bash
python scripts/verify/verify_commands.py
```

## Known Limits

- HTTP mode does not support UI-only operations (`list_sidebar_items`, `open_section`, `get_search_placeholder`)
- Selenium mode depends on the current Xiaomi Notes web DOM structure
- `serviceToken` expires periodically; re-login via `open_mi_cloud.py` when needed
- Search is client-side text filtering in both modes
- Private notes are intentionally unsupported
