# Examples

## Intent To Command Mapping

Use the existing command surface directly.

| Intent | Command | Required fields |
| --- | --- | --- |
| Read pending todos | `read-pending` | none |
| Read completed todos | `read-completed` | none |
| Create todo | `create` | `title` |
| Update todo title | `update` | `old_title`, `new_title` |
| Complete todo | `complete` | `title` |
| Restore todo | `restore` | `title` |
| Delete todo | `delete` | `title` |

## CLI Examples

```bash
python scripts/cli/run_skill.py minote-todo read-pending
python scripts/cli/run_skill.py minote-todo create --title "明天买咖啡豆"
python scripts/cli/run_skill.py minote-todo update --old-title "旧标题" --new-title "新标题"
python scripts/cli/run_skill.py minote-todo complete --title "洗衣服"
python scripts/cli/run_skill.py minote-todo restore --title "洗车"
python scripts/cli/run_skill.py minote-todo delete --title "剪头发"

python scripts/cli/mi_note_commands.py read-pending
python scripts/cli/mi_note_commands.py create "明天买咖啡豆"
python scripts/cli/mi_note_commands.py update "旧标题" "新标题"
python scripts/cli/mi_note_commands.py complete "洗衣服"
python scripts/cli/mi_note_commands.py restore "洗车"
python scripts/cli/mi_note_commands.py delete "剪头发"
```

## Python Examples

```python
from minote import execute_command

print(execute_command("read-pending"))
print(execute_command("create", title="测试待办"))
print(execute_command("update", old_title="旧标题", new_title="新标题"))
print(execute_command("complete", title="测试待办"))
```
