---
name: xsoar-xsiam-integration-builder
description: Builds complete XSOAR/XSIAM integrations from API documentation. Generates Python code, YAML definition, and developer documentation following Cortex XSOAR conventions. Also builds XSIAM event collectors that fetch logs/events from third-party APIs into XSIAM datasets.
---

# XSOAR/XSIAM Integration Builder

Generates production-ready XSOAR/XSIAM integrations when the user provides an API to integrate.

## Trigger Conditions

Invoke this skill when the user asks to:
- Build, create, write, or generate an XSOAR/XSIAM integration
- "Integrate [VendorName] with XSOAR/XSIAM"
- "Write an integration for [API]"
- Convert an API spec or documentation into an XSOAR integration
- Build an **event collector** — "fetch/ingest/collect [Vendor] logs or events into XSIAM", "pull audit logs into a dataset" (see Event Collector Mode below)

Do NOT invoke for questions about XSOAR in general — only for active integration building.

---

## Before Starting: Load Reference Materials

At the start of every integration build, read these files to load conventions and examples:

1. Read `~/.claude/skills/xsoar-xsiam-integration-builder/conventions.md` — coding conventions, required patterns, helper functions
2. Read `~/.claude/skills/xsoar-xsiam-integration-builder/yml-schema.md` — YAML field reference and type codes
3. Read `~/.claude/skills/xsoar-xsiam-integration-builder/examples/MalwareBazaar.py` — real marketplace integration: API key via header, file/hash reputation, multipart POST, DBotScore, Common.File indicator
4. Read `~/.claude/skills/xsoar-xsiam-integration-builder/examples/MalwareBazaar.yml` — matching YAML for MalwareBazaar
5. Read `~/.claude/skills/xsoar-xsiam-integration-builder/examples/Pulsedive.py` — real marketplace integration: API key as query param, IP/Domain/URL reputation commands, Common.IP/Domain/URL indicators, DBotScore
6. Read `~/.claude/skills/xsoar-xsiam-integration-builder/examples/Pulsedive.yml` — matching YAML for Pulsedive
7. If the integration requires **mirroring** (bidirectional sync between XSOAR incidents and remote tickets): Read `~/.claude/skills/xsoar-xsiam-integration-builder/examples/ServiceNowV2_Mirroring.py` and `~/.claude/skills/xsoar-xsiam-integration-builder/examples/ServiceNowV2_Mirroring.yml` — extracted from ServiceNow v2, the canonical mirroring reference in the XSOAR marketplace
8. If building an **event collector** (fetches logs/events into an XSIAM dataset): Read `~/.claude/skills/xsoar-xsiam-integration-builder/examples/HelloWorldEventCollector.py` and `~/.claude/skills/xsoar-xsiam-integration-builder/examples/HelloWorldEventCollector.yml` — the official Palo Alto template showing the canonical collector structure, and `~/.claude/skills/xsoar-xsiam-integration-builder/examples/OktaEventCollector.py` and `~/.claude/skills/xsoar-xsiam-integration-builder/examples/OktaEventCollector.yml` — a real-world collector with next-link pagination, ID-based deduplication, and 429 rate-limit handling

These are production integrations pulled directly from the Demisto/XSOAR content repository. Use them as your structural and stylistic baseline. Do not deviate from the patterns shown unless the API requires it.

---

## Phase 1: Gather Requirements

If the user has not already provided the following, ask before proceeding:

1. **Integration type** — A regular integration (commands + optional incident fetching) or an **event collector** (pulls raw logs/events from the vendor API into an XSIAM dataset). If the user says "fetch/ingest logs or events into XSIAM", it is an event collector — follow Event Collector Mode below.
2. **API documentation** — URL, pasted content, or uploaded file. You need: base URL, authentication method, available endpoints, request/response schemas.
3. **Integration name** — The vendor name, used as the prefix for all commands (e.g., `vendorname-get-alert`).
4. **Category** — Ask or infer from the API's purpose. See `yml-schema.md` for valid values. Event collectors are always `Analytics & SIEM`.
5. **Fetch incidents?** — Does the user want XSOAR to pull alerts/events as incidents automatically? (Not applicable to event collectors — they always fetch events.)
6. **Commands to implement** — If the API has many endpoints, confirm which ones to include. Default: implement all read/GET operations plus the most commonly used write operations. Event collectors implement only `test-module`, `fetch-events`, and `<vendor>-get-events`.

If the user provides a URL for API documentation, use WebFetch to retrieve it before proceeding.

---

## Phase 2: Analyze the API

Before writing any code:

1. Identify the **authentication scheme**: API key (header or query param), Bearer token, Basic auth, OAuth2, or custom.
2. List **all endpoints** you will implement, with HTTP method, path, parameters, and response shape.
3. Identify the **primary entity type** (alerts, events, incidents, indicators, findings, etc.) — this drives command naming.
4. Note **pagination** approach: limit/offset, cursor, page number, or none.
5. Note any **date/time fields** and their format (ISO 8601, Unix epoch, custom).
6. Identify the **natural fetch endpoint** if implementing incident fetching (usually a list endpoint that supports time-range filtering).

Briefly summarize your analysis to the user and confirm before generating code.

---

## Phase 3: Generate the Python Integration

Write `<VendorName>.py` following these rules exactly:

### Structure (in order)
1. Imports — standard library and third-party only (e.g., `import json`, `import time`). **Do NOT include** `import demistomock as demisto`, `from CommonServerPython import *`, or `from CommonServerUserPython import *` — these are injected automatically by the XSOAR runtime and must be omitted from the source.
2. Constants (`VENDOR_NAME`, `DEFAULT_MAX_RESULTS`, any static mappings)
3. `Client` class extending `BaseClient`
4. `test_module(client)` function
5. One function per command: `<action>_command(client, args) -> CommandResults`
6. `fetch_incidents(...)` if applicable
7. `main()` function
8. `if __name__` guard

### Rules
- All API calls inside `Client` methods via `self._http_request()`
- Use `assign_params()` to build param/body dicts — it drops None values automatically
- Use `arg_to_number()`, `arg_to_datetime()`, `arg_to_boolean()`, `argToList()` for arg parsing — never cast manually
- Use `tableToMarkdown()` for all `readable_output` — pass `removeNull=True` and `headerTransform=pascalToSpace`
- Return `CommandResults` from every command function — never return raw dicts or strings
- `outputs_key_field` must match the unique identifier field in the API response
- Catch `DemistoException` in `test_module` for auth-specific errors; let other exceptions bubble to `main()`
- `main()` wraps everything in `try/except Exception` and calls `return_error()` on failure
- Use `demisto.debug()` to log the command name at the start of `main()`
- API key can come from `params.get('apikey')` OR `params.get('credentials', {}).get('password')` — check both

---

## Phase 4: Generate the YAML Definition

Write `<VendorName>.yml` following these rules:

### Structure
- `category`: match the API's purpose to a valid XSOAR category
- `commonfields.id` and `name`: exact vendor name, no spaces
- `display`: human-readable name with spaces/proper casing
- `description`: one clear sentence describing what the integration does and its primary use case
- `configuration`: include URL, auth param(s), `insecure`, `proxy`. Add `isFetch`/`incidentType`/`first_fetch`/`max_fetch` if fetching incidents.
- `script.commands`: one entry per implemented command, matching Python functions 1:1
- `script.isfetch`: true if fetch_incidents is implemented
- `script.script`: leave as `''` for now — it will be replaced with the actual Python code in Phase 6
- `fromversion`: `'6.0.0'` unless you have a reason for a different version

### Choosing a Docker image

Before setting `dockerimage`, check the available images and their included packages at:
**https://github.com/demisto/dockerfiles-info/blob/master/used_packages.csv**

Use WebFetch to retrieve that CSV, identify which packages your integration needs (e.g., `requests`, `dateparser`, `cryptography`), and confirm they are present in the image you select. The standard `demisto/python3:3.x.x.xxxxxxx` image covers the vast majority of integrations — use it unless your integration requires a package that is only available in a specialised image (e.g., `demisto/boto3py3` for AWS SDK, `demisto/chromium` for browser automation). Always pick the latest available tag for the chosen image family.

### Command YAML rules
- Command `name` must exactly match the string used in `main()`'s `if command ==` block
- Every argument in the Python function must have a corresponding YAML argument entry
- Every `outputs_prefix` path in Python must have corresponding `outputs` entries in YAML
- Context paths: `VendorName.EntityType.field_name` — match the exact key names from API responses
- Use `predefined` lists for args with a fixed set of valid values (status, severity, type, etc.)
- Write clear, specific `description` for every argument and output — these appear in the UI

---

## Phase 5: Generate the README

Write `README.md` with these sections:

```markdown
# VendorName

## Overview
What the integration does and its primary use cases. 2-4 sentences.

## Prerequisites
- What the user must set up in the vendor platform before configuring the integration
- API key location, required permissions/scopes, IP allowlisting if needed

## Configuration
Table of all configuration parameters, their purpose, and where to find the values.

| Parameter | Description | Required |
|-----------|-------------|----------|
| Server URL | Base API URL | Yes |
| API Key | ... | Yes |

## Commands
One subsection per command:

### vendorname-get-alert
**Description:** ...

**Arguments:**
| Argument | Description | Required | Default |
|----------|-------------|----------|---------|

**Context Output:**
| Path | Type | Description |
|------|------|-------------|

**Example:**
`!vendorname-get-alert id="12345"`

## Incident Fetching (if applicable)
How the fetch works, what it pulls, how to configure the time window.

## Troubleshooting
Common errors and how to resolve them (auth failures, rate limits, SSL issues).
```

---

## Phase 5b: Mirroring (if required)

If the user wants bidirectional sync between XSOAR incidents and the remote system, implement mirroring using the ServiceNowV2_Mirroring reference files.

### When to add mirroring
- User asks for "mirroring", "two-way sync", "sync back to the source", or the integration manages tickets/cases/incidents in the remote system

### What to implement

**Python additions:**
1. `MIRROR_DIRECTION` constant mapping UI dropdown values to `"In"`, `"Out"`, `"Both"`, `None`
2. `get_mirroring()` helper — returns `mirror_direction`, `mirror_tags`, `mirror_instance` to attach to every fetched incident
3. `get_remote_data_command(client, args, params)` — pulls updated fields + new entries (comments, files) from the remote ticket; returns `[ticket_dict] + [entry_dicts]`
4. `update_remote_system_command(client, args, params)` — pushes delta fields and outbound-tagged entries to the remote; returns the remote ID string
5. `get_modified_remote_data_command(client, args)` — queries remote for IDs modified since `lastUpdate`; returns `GetModifiedRemoteDataResponse(list_of_ids)`
6. Wire all three into `main()`

**YAML additions:**
- `script.ismappable: true`
- `script.isremotesyncin: true`
- `script.isremotesyncout: true`
- Mirror configuration params: `mirror_direction`, `comment_tag`, `comment_tag_from_<vendor>`, `file_tag`, `file_tag_from_<vendor>`, `mirror_limit`, `close_incident`, `close_ticket`
- Three mirror commands in `script.commands`: `get-remote-data`, `update-remote-system`, `get-modified-remote-data`

---

## Event Collector Mode (XSIAM log/event ingestion)

Use this mode when the goal is to pull raw logs/events from a third-party API into an **XSIAM dataset** (not to create incidents or run enrichment commands). Phases 1, 2, 5, and 6 still apply; this section replaces the Phase 3 and Phase 4 instructions. Read the HelloWorldEventCollector and OktaEventCollector example files listed in the reference materials before generating code.

### Naming and scope
- Integration ID/name: `<VendorName>EventCollector`; display name: `<Vendor> Event Collector`
- Category is always `Analytics & SIEM`
- Exactly three commands: `test-module`, `fetch-events`, and a manual `<vendor>-get-events` command. No enrichment commands, no incident fetching, no context outputs.
- Events land in the XSIAM dataset `<vendor>_<product>_raw` — derived from the `VENDOR` and `PRODUCT` constants. Confirm these values with the user (lowercase, e.g., vendor `okta`, product `okta`).

### Python structure (replaces Phase 3 structure)
1. Constants: `VENDOR`, `PRODUCT`, `DATE_FORMAT`, page-size/fetch limits
2. `Client(BaseClient)` — one method to query the events endpoint, supporting a start time, a limit, and the API's pagination token/next-link
3. `test_module(...)` — performs a 1-event dry-run fetch; returns `'ok'`
4. `get_events(...)` — used by the manual command; returns `(events, CommandResults)` with `tableToMarkdown` readable output
5. `fetch_events(client, last_run, first_fetch_time, max_events_per_fetch)` — returns `(next_run, events)`
6. `add_time_to_events(events)` — sets `event['_time']` from the event's creation timestamp (use `arg_to_datetime`); called before every send
7. `main()` wiring:

```python
elif command == 'fetch-events':
    last_run = demisto.getLastRun()
    next_run, events = fetch_events(client, last_run, first_fetch_time, max_events_per_fetch)
    add_time_to_events(events)
    send_events_to_xsiam(events, vendor=VENDOR, product=PRODUCT)
    demisto.setLastRun(next_run)

elif command == '<vendor>-get-events':
    should_push_events = argToBoolean(args.pop('should_push_events'))
    events, results = get_events(client, args)
    return_results(results)
    if should_push_events:
        add_time_to_events(events)
        send_events_to_xsiam(events, vendor=VENDOR, product=PRODUCT)
```

### Fetch logic rules
- `send_events_to_xsiam()` comes from CommonServerPython — never implement the HTTP push yourself.
- **Checkpointing:** store the timestamp of the newest fetched event in `last_run` and query from it on the next run. On first run, fall back to the `first_fetch` / `after` config param (parse with `dateparser.parse` or `arg_to_datetime`).
- **Deduplication:** if the API filter is inclusive of the boundary timestamp, also store the IDs of all events sharing the newest timestamp in `last_run` and drop those IDs from the next fetch (see `remove_duplicates` / `get_last_run` in OktaEventCollector.py).
- **Pagination:** loop pages until `max_events_per_fetch` is reached or no more results; persist the next-page token/link in `last_run` if the fetch stops mid-stream.
- **Rate limits:** on HTTP 429, return the events collected so far rather than failing; honor any rate-limit-reset header if the wait is short (see OktaEventCollector.py).
- Sort/request events in ascending time order so checkpointing is correct.
- Use `demisto.debug()` liberally — fetch counts, last_run contents, pagination decisions.
- **OAuth note:** content-repo collectors for Microsoft/Graph-style APIs use `MicrosoftApiModule`/`SiemApiModule`, which are merged at build time in the demisto/content repo and are **not available to custom uploaded integrations**. For a client-credentials flow, implement the token request directly in `Client` (POST to the token endpoint, cache the token and its expiry in `demisto.getIntegrationContext()`).

### YAML structure (replaces Phase 4 structure)
- `script.isfetchevents: true` (instead of `isfetch`)
- `marketplaces: [marketplacev2, platform]` and `supportedModules: [xsiam]` — collectors are XSIAM-only
- `sectionorder: [Connect, Collect]` at top level; every configuration param gets a `section: Connect` (URL, auth, insecure, proxy) or `section: Collect` (first-fetch time, max events per fetch)
- Standard Collect params: `max_events_per_fetch` (or `limit`) and a first-fetch param (e.g., `after`, type 15 with predefined ranges, or a free-text `first_fetch`)
- The `<vendor>-get-events` command must define a required `should_push_events` boolean argument (`auto: PREDEFINED`, values 'true'/'false', default 'false') plus optional `limit`/`from_date` arguments. No `outputs`.
- `fromversion: 6.8.0` or later (use `8.4.0` if unsure)
- See the Event Collector section of `yml-schema.md` and both example `.yml` files for the exact shape

### README additions
In addition to the Phase 5 sections, document:
- The target dataset name (`<vendor>_<product>_raw`)
- How checkpointing works and what the first-fetch param controls
- That `<vendor>-get-events` with `should_push_events=false` is the safe way to test without writing to the dataset

---

## Phase 6: Embed Python Code into the YAML

**This step is mandatory for every integration build.** XSOAR's upload-ready format is a single unified YAML file with the Python source embedded in `script.script` as a literal block scalar. Without this step the integration cannot be imported directly into XSOAR.

After both `<VendorName>.py` and `<VendorName>.yml` are written to disk, run the following Python snippet via the Bash tool to inject the code:

```python
with open('<VendorName>.py', 'r') as f:
    py_code = f.read()

with open('<VendorName>.yml', 'r') as f:
    yml = f.read()

# Indent every line 4 spaces for the YAML block scalar
indented = '\n'.join('    ' + line if line else '' for line in py_code.split('\n'))
indented = indented.rstrip()

# Replace the placeholder with the literal block scalar + indented code
updated = yml.replace("  script: ''", '  script: |-\n' + indented)

with open('<VendorName>.yml', 'w') as f:
    f.write(updated)
```

**How the embedding works:**
- `script: |-` is a YAML literal block scalar: `|` preserves newlines, `-` strips the trailing newline.
- All Python lines are indented 4 spaces. YAML strips that base indentation automatically, so the Python code is preserved exactly — 0-space top-level, 4-space class bodies, 8-space method bodies, etc.
- The `subtype`, `type`, `feed`, and other sibling keys that follow in the YAML remain at 2-space indent, so YAML correctly reads them as siblings of `script:`, not as part of the code block.
- The `.py` file should be kept alongside the `.yml` as the developer-editable source. The `.yml` is the deployment artifact.

---

## Output

Produce all files in sequence. For each file, state the filename clearly then output the full content in a code block. Create the actual files on disk in a directory named after the integration:

```
<VendorName>/
  <VendorName>.py       ← developer source
  <VendorName>.yml      ← deployment artifact (Python embedded in script.script)
  README.md
```

After creating all files and completing Phase 6, summarize:
1. Which commands were implemented
2. Whether incident fetching is included
3. Any assumptions made about the API (e.g., auth header name, pagination approach)
4. Any API endpoints that were excluded and why

---

## Quality Checklist

Before declaring the integration complete, verify:
- [ ] `test-module` is implemented and returns `'ok'` on success
- [ ] Every command in `main()` if/elif block has a matching YAML command entry
- [ ] All YAML context paths match the actual Python `outputs_prefix` values
- [ ] `outputs_key_field` is set to the correct unique ID field
- [ ] Auth param supports both plain string and credentials object patterns
- [ ] `base_url` has trailing slash stripped
- [ ] `verify_certificate` correctly inverts the `insecure` param
- [ ] README documents every command and all configuration parameters
- [ ] **Phase 6 completed: Python code is embedded in `script.script` as an indented `|-` block scalar in the YAML**

Event collectors only:
- [ ] `script.isfetchevents: true`, `marketplaces: [marketplacev2, platform]`, `supportedModules: [xsiam]` are set
- [ ] Every event is given a `_time` field before `send_events_to_xsiam()` is called
- [ ] `last_run` checkpointing dedups events at the boundary timestamp (no duplicated or dropped events across fetches)
- [ ] `<vendor>-get-events` has a required `should_push_events` argument and only pushes when it is true
- [ ] README states the target dataset name (`<vendor>_<product>_raw`)
