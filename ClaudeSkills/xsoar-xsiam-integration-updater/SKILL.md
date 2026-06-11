---
name: xsoar-xsiam-integration-updater
description: Updates an existing XSOAR/XSIAM integration — modifies the Python source, syncs the YAML definition to match, updates the README, and re-embeds the Python into the deployment-ready YAML.
---

# XSOAR/XSIAM Integration Updater

Updates an existing XSOAR/XSIAM integration that was previously built (typically with the `xsoar-xsiam-integration-builder` skill). Handles Python changes, YAML sync, README updates, and re-embedding the Python into the unified YAML artifact.

## Trigger Conditions

Invoke this skill when the user asks to:
- Add a new command or endpoint to an existing integration
- Remove or rename a command
- Change arguments, outputs, or behavior of an existing command
- Fix a bug in integration code
- Update authentication logic
- Sync a YAML or README that has drifted from the Python

Do NOT invoke for building a brand-new integration from scratch — use `xsoar-xsiam-integration-builder` for that.

---

## Before Starting: Load Reference Materials

1. Read `~/.claude/skills/xsoar-xsiam-integration-builder/conventions.md` — coding conventions shared with the builder skill
2. Read `~/.claude/skills/xsoar-xsiam-integration-builder/yml-schema.md` — YAML field reference and type codes

---

## Phase 1: Read the Existing Integration

Before making any changes, read all three files in the integration directory:

1. `<IntegrationName>.py` — the Python source
2. `<IntegrationName>.yml` — the YAML definition (which contains the embedded Python in `script.script`)
3. `README.md` — the command reference documentation

If the user has not provided the directory path, ask for it.

---

## Phase 2: Understand the Change Request

Analyze what the user wants to change. Categorize each change:

| Change type | What it affects |
|---|---|
| New command/endpoint | Python + YAML commands block + README |
| Removed command | Python + YAML commands block + README |
| Renamed command | Python dispatch table + YAML command `name` + README |
| Modified arguments | Python command function + YAML command `arguments` + README |
| Modified outputs / context paths | Python `CommandResults` + YAML `outputs` + README |
| Auth / client changes | Python only (unless config params change) |
| Bug fix with no signature change | Python only |

Summarize the planned changes to the user before proceeding. If the scope is unclear, ask.

---

## Phase 3: Update the Python File

Edit `<IntegrationName>.py` following these rules:

- **New command**: add a `Client` method + a `_command` function + an entry in the `commands` dispatch dict in `main()`
- **Removed command**: remove the `Client` method, `_command` function, and dispatch entry
- **Renamed command**: update the dispatch dict key and the README — the function name can stay the same
- Do NOT include `import demistomock as demisto`, `from CommonServerPython import *`, or `from CommonServerUserPython import *` — these are injected by the XSOAR runtime
- Follow all conventions from `conventions.md`: `assign_params()`, `arg_to_number()`, `tableToMarkdown()`, `CommandResults`, etc.
- Keep the `if __name__` guard at the bottom

### Verify Python is self-consistent after editing

Run this check to confirm the dispatch table and function definitions are in sync:

```bash
# Commands in the dispatch dict
grep "'criblapi-" <IntegrationName>.py | grep "_command,"

# Command functions defined
grep "^def .*_command(" <IntegrationName>.py
```

Every entry in the dispatch dict must have a matching function definition.

---

## Phase 4: Sync the YAML Commands Block

After the Python is updated, diff the commands in the Python dispatch table against the YAML command entries:

```bash
# Commands in Python dispatch table
grep "'<prefix>-" <IntegrationName>.py | grep "_command,"

# Commands in YAML
grep "^  - name:" <IntegrationName>.yml
```

For each discrepancy:

- **In Python but not in YAML** → add a full command entry to the YAML `script.commands` block
- **In YAML but not in Python** → remove the command entry from the YAML
- **Arguments changed** → update the YAML `arguments` list for that command
- **Outputs changed** → update the YAML `outputs` list for that command

### YAML command entry rules
- `name` must exactly match the string key in the Python dispatch dict
- Every argument in the Python `_command` function must have a YAML `arguments` entry
- Every `outputs_prefix` context path in Python must have a matching YAML `outputs` entry
- Use `predefined` for fixed-value arguments
- Write clear `description` for every argument and output — these appear in the XSOAR UI

---

## Phase 5: Update the README

Sync `README.md` to reflect all changes made in Phases 3 and 4:

- **New command** → add a full subsection with description, arguments table, context output table, and example
- **Removed command** → delete its subsection
- **Changed arguments or outputs** → update the relevant tables
- **Changed auth or configuration** → update the Prerequisites and Configuration sections

Keep existing sections that were not affected by the change.

---

## Phase 6: Re-embed the Python into the YAML

**This step is mandatory after every update, even if only the YAML commands block changed.** The `script.script` field in the YAML must always reflect the current state of the `.py` file.

Run the following via the Bash tool from the integration directory:

```python
import re

with open('<IntegrationName>.py', 'r') as f:
    py_code = f.read()

with open('<IntegrationName>.yml', 'r') as f:
    yml = f.read()

# Strip any previously embedded block
yml = re.sub(r"  script: \|-\n(    [^\n]*\n|\n)*", "  script: ''\n", yml)

# Re-embed
indented = '\n'.join('    ' + line if line else '' for line in py_code.split('\n'))
indented = indented.rstrip()
updated = yml.replace("  script: ''", '  script: |-\n' + indented)

with open('<IntegrationName>.yml', 'w') as f:
    f.write(updated)

# Verify command parity
py_commands = sorted(set(
    line.split("'")[1] for line in py_code.split('\n')
    if line.strip().startswith("'") and '_command' in line and ':' in line
))
yml_commands = sorted(
    line.strip().replace('- name: ', '')
    for line in updated.split('\n')
    if line.strip().startswith('- name: ')
)
print(f'Python commands: {len(py_commands)}')
print(f'YAML commands:   {len(yml_commands)}')
missing_from_yml = set(py_commands) - set(yml_commands)
missing_from_py  = set(yml_commands) - set(py_commands)
if missing_from_yml:
    print('MISSING from YAML:', missing_from_yml)
if missing_from_py:
    print('MISSING from Python:', missing_from_py)
if not missing_from_yml and not missing_from_py:
    print('All commands in sync.')
```

Do not declare the update complete until the script reports **"All commands in sync."**

---

## Quality Checklist

Before declaring the update complete, verify:

- [ ] All changed Python functions follow conventions from `conventions.md`
- [ ] Every new command in the Python dispatch dict has a matching YAML command entry
- [ ] Every removed command has been removed from both Python and YAML
- [ ] All YAML `arguments` entries match the actual args read in the Python `_command` functions
- [ ] All YAML `outputs` context paths match the `outputs_prefix` values in Python `CommandResults`
- [ ] README reflects all additions, removals, and changes
- [ ] Phase 6 embed script ran and reported **"All commands in sync."**
