# XSOAR/XSIAM Integration Builder — Setup & Usage Guide

This skill gives Claude Code the ability to generate production-ready XSOAR/XSIAM integrations from an API spec or documentation. It handles Python code, YAML definition, README, and embedding the code into the deployment-ready unified YAML format.

---

## Directory Structure

```
xsoar-xsiam-integration-builder/
├── SKILL.md                        ← skill instructions (loaded by Claude Code)
├── HOW_TO_USE.md                   ← this file
├── conventions.md                  ← XSOAR coding conventions reference
├── yml-schema.md                   ← YAML field and type code reference
└── examples/
    ├── MalwareBazaar.py
    ├── MalwareBazaar.yml
    ├── Pulsedive.py
    ├── Pulsedive.yml
    ├── ServiceNowV2_Mirroring.py
    └── ServiceNowV2_Mirroring.yml
```

---

## Installation

### Step 1 — Locate your Claude Code skills directory

Skills live in `~/.claude/skills/` on your machine. Create it if it doesn't exist:

```bash
mkdir -p ~/.claude/skills
```

### Step 2 — Copy the skill folder

Copy the entire `xsoar-xsiam-integration-builder/` directory into `~/.claude/skills/`:

```bash
cp -r xsoar-xsiam-integration-builder/ ~/.claude/skills/
```

Your final structure should look like:

```
~/.claude/skills/
└── xsoar-xsiam-integration-builder/
    ├── SKILL.md
    ├── HOW_TO_USE.md
    ├── conventions.md
    ├── yml-schema.md
    └── examples/
        └── ...
```

### Step 3 — Verify Claude Code can see it

Open Claude Code and type `/` — you should see `xsoar-xsiam-integration-builder` appear in the slash-command autocomplete list.

---

## Usage

### Invoke the skill

In any Claude Code session, type:

```
/xsoar-xsiam-integration-builder
```

Claude will load the skill and prompt you for the information it needs to build the integration.

### What you'll be asked

| Question | Example answer |
|---|---|
| API documentation | Path to a local spec file, a URL, or paste the content directly |
| Integration name | `Cribl API` |
| Category | `IT Services` (or leave blank to let Claude infer) |
| Fetch incidents? | `No` |
| Which commands to implement | `All` or list specific endpoints |

### What gets generated

Claude will produce three files inside a directory named after the integration:

```
<IntegrationName>/
├── <IntegrationName>.py     ← developer-editable Python source
├── <IntegrationName>.yml    ← upload-ready YAML with Python embedded
└── README.md                ← command reference and configuration guide
```

The `.yml` file is the deployment artifact — it can be imported directly into XSOAR/XSIAM via **Settings > Integrations > Upload**.

---

## Importing into XSOAR/XSIAM

1. In XSOAR/XSIAM, go to **Settings > Integrations**.
2. Click **Upload** (top right).
3. Select the generated `<IntegrationName>.yml` file.
4. The integration will appear in your integrations list. Click **Add instance** to configure it.

---

## Tips

- **Large API specs**: For specs with hundreds of endpoints (e.g., an OpenAPI YAML), Claude will ask which endpoint groups to implement. You can say `all` or name specific categories (e.g., `just the sources, destinations, and jobs endpoints`).
- **OAuth2 / token expiry**: If the API uses OAuth2 client credentials, mention it or point Claude to an existing integration file that shows the auth pattern. Claude will implement token caching via `get_integration_context()` / `set_integration_context()` automatically.
- **Editing after generation**: Make all edits to the `.py` file (the readable source), then re-run the Phase 6 embed snippet from `SKILL.md` to sync changes back into the `.yml`.
- **Docker image**: Claude will check [https://github.com/demisto/dockerfiles-info/blob/master/used_packages.csv](https://github.com/demisto/dockerfiles-info/blob/master/used_packages.csv) to confirm the chosen Docker image has the packages your integration needs.
