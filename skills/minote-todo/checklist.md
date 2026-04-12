# Minimal Workflow Checklist

## Before Running

- Confirm Chrome is installed.
- Confirm `bin/chromedriver.exe` matches the installed Chrome version.
- Confirm `selenium` is installed.
- Confirm a valid Xiaomi login session exists in `chrome_profile/`.

## First-Time Setup

1. Run `python scripts/cli/open_mi_cloud.py`.
2. Log in manually.
3. Close the browser after the session is saved.

## Execution Flow

1. Map the requested action to one of the supported commands.
2. Validate required fields.
3. Prefer executing through `python scripts/cli/run_skill.py minote-todo ...`.
4. Return the raw backend result.
5. If the operation fails, check login state and selector stability first.

## Verification

1. Run `python scripts/verify/verify_todo_crud.py`.
2. Run `python scripts/verify/verify_commands.py`.
