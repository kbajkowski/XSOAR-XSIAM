# XSOAR/XSIAM Integration YAML Schema

The YAML file is the complete integration definition. The Python code is embedded inside `script.script`.

---

## Top-Level Structure

```yaml
category: <category>           # See Category Values below
commonfields:
  id: <IntegrationName>        # Unique ID, no spaces
  version: -1                  # Always -1 for new integrations
configuration: [...]           # Auth and connection params — see Configuration section
description: <string>          # One-sentence description shown in marketplace
display: <Display Name>        # Human-readable name shown in UI
name: <IntegrationName>        # Must match commonfields.id
script:
  commands: [...]              # List of commands — see Command section
  runonce: false               # true only for one-shot utility integrations
  script: ''                   # Leave empty — populated by demisto-sdk on pack
  subtype: python3
  type: python
  feed: false                  # true if this is a threat intel feed
  isfetch: false               # true if this fetches incidents
  longRunning: false           # true if integration runs a long-running process
fromversion: '6.0.0'           # Minimum XSOAR version required
tests:
- No tests                     # Use "No tests" unless you have a test playbook name
```

---

## Category Values

Choose the most specific match:
- `Analytics & SIEM`
- `Authentication & Identity Management`
- `Case Management`
- `Data Enrichment & Threat Intelligence`
- `Database`
- `Email Gateway`
- `Endpoint`
- `Forensics & Malware Analysis`
- `IT Services`
- `Network Security`
- `Utilities`
- `Vulnerability Management`

---

## Configuration Parameters

Each entry in `configuration` is a parameter shown in the integration settings UI.

```yaml
configuration:
- defaultvalue: https://api.vendor.com/v1
  display: Server URL
  name: url
  required: true
  type: 0                   # Short text
  additionalinfo: The base URL for the API endpoint.

- display: API Key
  name: apikey
  required: true
  type: 4                   # Encrypted string (shown as password field)
  additionalinfo: The API key for authentication.

- display: Username
  name: credentials
  required: false
  type: 9                   # Credentials (username + password pair)

- display: Trust any certificate (not secure)
  name: insecure
  required: false
  type: 8                   # Boolean checkbox
  defaultvalue: 'false'

- display: Use system proxy settings
  name: proxy
  required: false
  type: 8                   # Boolean checkbox
  defaultvalue: 'false'

- defaultvalue: '50'
  display: Maximum number of incidents per fetch
  name: max_fetch
  required: false
  type: 0
  additionalinfo: Maximum is 200.

- defaultvalue: 3 days
  display: First fetch time
  name: first_fetch
  required: false
  type: 0
  additionalinfo: "Format: <number> <time unit>. E.g. 12 hours, 7 days."

- display: Incident type
  name: incidentType
  required: false
  type: 13                  # Choose-from-list (populated by XSOAR)

- display: Fetch incidents
  name: isFetch
  required: false
  type: 8
```

### Parameter Type Codes

| Code | Type | Use For |
|------|------|---------|
| 0 | Short text | URLs, free text, numbers as strings |
| 4 | Encrypted | API keys, tokens, passwords (single field) |
| 8 | Boolean | Checkboxes (insecure, proxy, fetch) |
| 9 | Credentials | Username + password pairs |
| 12 | Long text | Multi-line text (e.g. certificate content) |
| 13 | Single select | Dropdown lists |

---

## Commands

```yaml
script:
  commands:
  - name: vendorname-get-alert           # kebab-case, prefix with vendor name
    description: Retrieves a specific alert by its ID.
    arguments:
    - name: id
      description: The unique ID of the alert to retrieve.
      required: true
    - name: fields
      description: Comma-separated list of fields to include in the response.
      required: false
      isArray: false        # true if the arg accepts multiple values
      defaultValue: ''
      predefined:           # optional: constrain to specific values
      - ''
    outputs:
    - contextPath: VendorName.Alert.ID
      description: Unique identifier of the alert.
      type: String
    - contextPath: VendorName.Alert.Name
      description: Name or title of the alert.
      type: String
    - contextPath: VendorName.Alert.Severity
      description: Severity level of the alert.
      type: String
    - contextPath: VendorName.Alert.Status
      description: Current status of the alert.
      type: String
    - contextPath: VendorName.Alert.CreatedAt
      description: Timestamp when the alert was created.
      type: Date
    - contextPath: VendorName.Alert.UpdatedAt
      description: Timestamp when the alert was last updated.
      type: Date
```

### Argument Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | yes | Argument name (snake_case) |
| `description` | yes | What this argument does |
| `required` | no | Default false |
| `isArray` | no | True if comma-separated list accepted |
| `defaultValue` | no | Default value string |
| `predefined` | no | List of allowed values (creates dropdown) |
| `secret` | no | True to mask the value in logs |

### Output Type Values

| Type | Use For |
|------|---------|
| `String` | Text values |
| `Number` | Integers and floats |
| `Boolean` | True/false |
| `Date` | ISO 8601 timestamps |
| `Unknown` | Nested objects or arrays |

---

## Fetch Incidents Configuration

When `isfetch: true`, add these params and commands:

```yaml
configuration:
- display: Fetch incidents
  name: isFetch
  type: 8
  required: false

- display: Incident type
  name: incidentType
  type: 13
  required: false

- defaultvalue: 3 days
  display: First fetch time
  name: first_fetch
  type: 0
  required: false

- defaultvalue: '50'
  display: Maximum number of incidents per fetch
  name: max_fetch
  type: 0
  required: false
  additionalinfo: Maximum value is 200.

script:
  isfetch: true
```

---

## Event Collector Configuration (XSIAM)

Event collectors fetch raw logs/events into an XSIAM dataset. They use `isfetchevents`
(not `isfetch`), are XSIAM-only, and group their params into Connect/Collect sections:

```yaml
category: Analytics & SIEM
sectionorder:
- Connect
- Collect
commonfields:
  id: VendorNameEventCollector
  version: -1
name: VendorNameEventCollector
display: VendorName Event Collector
description: Collects audit and authentication events from VendorName.
configuration:
- display: Server URL
  name: url
  type: 0
  required: true
  section: Connect
- displaypassword: API Key
  name: credentials
  hiddenusername: true
  type: 9
  required: true
  section: Connect
- display: First fetch time
  name: first_fetch
  type: 0
  defaultvalue: 3 days
  required: false
  section: Collect
- display: Maximum number of events per fetch
  name: max_events_per_fetch
  type: 0
  defaultvalue: '1000'
  required: false
  section: Collect
- display: Trust any certificate (not secure)
  name: insecure
  type: 8
  required: false
  section: Connect
  advanced: true
- display: Use system proxy settings
  name: proxy
  type: 8
  required: false
  section: Connect
  advanced: true
script:
  commands:
  - name: vendorname-get-events
    description: Manual command to fetch events and display them.
    arguments:
    - name: should_push_events
      description: If true, the command will create events, otherwise it will only display them.
      required: true
      auto: PREDEFINED
      predefined:
      - 'true'
      - 'false'
      defaultValue: 'false'
    - name: limit
      description: Maximum number of results to return.
      required: false
    - name: from_date
      description: Date from which to get events.
      required: false
  isfetchevents: true
  runonce: false
  script: ''
  subtype: python3
  type: python
marketplaces:
- marketplacev2
- platform
supportedModules:
- xsiam
fromversion: 6.8.0
tests:
- No tests
```

Notes:
- `section: Connect` for connection/auth params, `section: Collect` for fetch-behavior params.
- The get-events command has no `outputs` — events go to the dataset, not the context.
- `fetch-events` and `test-module` are not declared in `commands`; `isfetchevents: true` enables them.
- The dataset name is `<vendor>_<product>_raw`, taken from the `send_events_to_xsiam()` call in the code.

---

## Complete Minimal Example

```yaml
category: Data Enrichment & Threat Intelligence
commonfields:
  id: VendorName
  version: -1
configuration:
- defaultvalue: https://api.vendor.com/v1
  display: Server URL
  name: url
  required: true
  type: 0
- display: API Key
  name: apikey
  required: true
  type: 4
- display: Trust any certificate (not secure)
  name: insecure
  required: false
  type: 8
- display: Use system proxy settings
  name: proxy
  required: false
  type: 8
description: VendorName integration for threat intelligence enrichment.
display: VendorName
name: VendorName
script:
  commands:
  - name: vendorname-get-alert
    description: Retrieves a specific alert by its ID.
    arguments:
    - name: id
      description: The unique ID of the alert.
      required: true
    outputs:
    - contextPath: VendorName.Alert.ID
      description: Alert ID.
      type: String
  runonce: false
  script: ''
  subtype: python3
  type: python
  feed: false
  isfetch: false
fromversion: '6.0.0'
tests:
- No tests
```
