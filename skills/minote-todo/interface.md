# Interface

## Contract

This skill is command-oriented.

Inputs should be mapped to one of the existing command names exposed by `minote.execute_command` or `scripts/cli/mi_note_commands.py`.

The preferred external entrypoint for agents is `scripts/cli/run_skill.py`.

## Input Schema

Base shape:

```json
{
  "command": "create",
  "args": {
    "title": "测试待办"
  }
}
```

Equivalent CLI shape:

```bash
python scripts/cli/run_skill.py minote-todo <command> [flags]
```

Supported commands:

```json
[
  { "command": "read-pending", "args": {} },
  { "command": "read-completed", "args": {} },
  { "command": "create", "args": { "title": "string" } },
  { "command": "update", "args": { "old_title": "string", "new_title": "string" } },
  { "command": "complete", "args": { "title": "string" } },
  { "command": "restore", "args": { "title": "string" } },
  { "command": "delete", "args": { "title": "string" } }
]
```

## Output Shape

Unified skill runner returns:

```json
{
  "skill": "minote-todo",
  "result": {
    "command": "create",
    "title": "测试待办",
    "ok": true
  }
}
```

Read commands return:

```json
{
  "command": "read-pending",
  "items": [
    {
      "title": "买咖啡豆",
      "counter": "",
      "remind": "",
      "status": "pending"
    }
  ]
}
```

Mutation commands return:

```json
{
  "command": "create",
  "title": "测试待办",
  "ok": true
}
```

## Failure Handling

- If login state is missing, first run `python scripts/cli/open_mi_cloud.py` and complete manual login.
- If a todo is not found, mutation commands may return `ok: false`.
- If selectors drift because the Xiaomi page changed, inspect `src/minote/client.py` before adding new abstraction layers.
- If the command itself is unsupported, the backend raises `ValueError`.
