# MiNote Todo Skill

## Purpose

This skill wraps the existing MiNote Selenium automation as a reusable local capability.

Use it when the user wants to operate Xiaomi Cloud Notes todos through the already-implemented local framework instead of building a natural-language parser.

## Scope

Supported operations:

- Read pending todos
- Read completed todos
- Create a todo
- Update a todo title
- Complete a todo
- Restore a completed todo
- Delete a todo

Explicitly out of scope:

- Private notes
- Private-note search and read
- Building a Chinese natural-language parser

## Runtime Assumptions

- Windows machine
- Google Chrome is installed
- `bin/chromedriver.exe` matches the local Chrome version
- The project-local browser profile is stored in `chrome_profile/`
- The operator can log in manually the first time if the login state is missing

## Project Entry Points

- Browser launcher: `scripts/cli/open_mi_cloud.py`
- Unified skill runner: `scripts/cli/run_skill.py`
- CLI commands: `scripts/cli/mi_note_commands.py`
- Client API: `src/minote/client.py`
- Command executor: `src/minote/commands.py`
- Detailed API notes: `API.md`
- Interface contract: `skills/minote-todo/interface.md`
- Usage examples: `skills/minote-todo/examples.md`
- Execution checklist: `skills/minote-todo/checklist.md`

## Recommended Workflow

1. If login state may be missing or expired, run:

```bash
python scripts/cli/open_mi_cloud.py
```

2. After the user finishes manual login, use the command runner:

```bash
python scripts/cli/run_skill.py minote-todo read-pending
python scripts/cli/run_skill.py minote-todo create --title "明天下午买咖啡豆"
python scripts/cli/run_skill.py minote-todo update --old-title "旧标题" --new-title "新标题"
python scripts/cli/run_skill.py minote-todo complete --title "洗衣服"
python scripts/cli/run_skill.py minote-todo restore --title "洗车"
python scripts/cli/run_skill.py minote-todo delete --title "剪头发"

python scripts/cli/mi_note_commands.py read-pending
python scripts/cli/mi_note_commands.py read-completed
python scripts/cli/mi_note_commands.py create "明天下午买咖啡豆"
python scripts/cli/mi_note_commands.py update "旧标题" "新标题"
python scripts/cli/mi_note_commands.py complete "洗衣服"
python scripts/cli/mi_note_commands.py restore "洗车"
python scripts/cli/mi_note_commands.py delete "剪头发"
```

3. For Python-level integration, prefer:

```python
from minote import execute_command

result = execute_command("create", title="测试待办")
print(result)
```

## Guidance For Future Skill Integration

- Treat this repository as the execution backend.
- Do not add a natural-language parser unless the user explicitly asks for one.
- Prefer mapping structured user intent directly to existing command names.
- Reuse the current command surface before introducing new abstractions.
- If an operation fails, verify login state and current DOM stability first.

## Standard Operating Rules

- Prefer direct command mapping over natural-language parsing.
- Return backend results with minimal reshaping.
- Treat `ok: false` as an execution failure that needs operator-facing context.
- Do not claim support for private notes.
- Do not change the underlying browser automation flow unless verification shows breakage.

## Validation

Useful verification scripts:

```bash
python scripts/verify/verify_todo_crud.py
python scripts/verify/verify_commands.py
```
