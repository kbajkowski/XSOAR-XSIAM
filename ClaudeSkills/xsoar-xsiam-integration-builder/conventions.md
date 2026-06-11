# XSOAR/XSIAM Integration Coding Conventions

## Client Class

Every integration has a `Client` class that extends `BaseClient`. This handles authentication, proxy, and SSL automatically.

```python
class Client(BaseClient):
    def __init__(self, base_url: str, api_key: str, verify: bool, proxy: bool):
        super().__init__(
            base_url=base_url,
            verify=verify,
            proxy=proxy,
            headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
        )

    def get_alert(self, alert_id: str) -> dict:
        return self._http_request(method='GET', url_suffix=f'/alerts/{alert_id}')

    def list_alerts(self, limit: int, status: str | None = None) -> dict:
        params: dict = {'limit': limit}
        if status:
            params['status'] = status
        return self._http_request(method='GET', url_suffix='/alerts', params=params)
```

Rules:
- All API calls go through `self._http_request()`, never `requests.get()` etc.
- Method signature: `method`, `url_suffix`, `params={}`, `json_data={}`, `headers={}`
- `_http_request` raises `DemistoException` on non-2xx responses automatically
- Use `ok_codes` param to override acceptable status codes when needed

---

## Command Functions

Each command is a standalone function that takes a `client: Client` and `args: dict`.

```python
def get_alert_command(client: Client, args: dict) -> CommandResults:
    alert_id = args.get('id', '')
    response = client.get_alert(alert_id)

    return CommandResults(
        outputs_prefix='VendorName.Alert',
        outputs_key_field='ID',
        outputs=response,
        readable_output=tableToMarkdown('Alert', response),
        raw_response=response
    )
```

Rules:
- Always return `CommandResults` (not dicts, not strings)
- `outputs_prefix` matches the context path in the YAML
- `outputs_key_field` is the unique identifier field name (used for dedup in context)
- `readable_output` uses `tableToMarkdown()` for structured data
- Pass `raw_response` for transparency

---

## main() Function

```python
def main() -> None:
    params = demisto.params()
    args = demisto.args()
    command = demisto.command()

    base_url = params.get('url', '').rstrip('/')
    api_key = params.get('apikey') or (params.get('credentials') or {}).get('password', '')
    verify_certificate = not params.get('insecure', False)
    proxy = params.get('proxy', False)

    demisto.debug(f'Command being called is {command}')

    try:
        client = Client(
            base_url=base_url,
            api_key=api_key,
            verify=verify_certificate,
            proxy=proxy,
        )

        if command == 'test-module':
            return_results(test_module(client))
        elif command == 'vendorname-get-alert':
            return_results(get_alert_command(client, args))
        elif command == 'vendorname-list-alerts':
            return_results(list_alerts_command(client, args))
        else:
            raise NotImplementedError(f'Command {command} is not implemented')

    except Exception as e:
        return_error(f'Failed to execute {command} command.\nError:\n{str(e)}')


if __name__ in ('__main__', '__builtin__', 'builtins'):
    main()
```

Rules:
- Always strip trailing `/` from `base_url`
- API key can come from a plain string param OR from a credentials object — check both
- `verify_certificate` inverts `insecure`
- Use `return_results()` for success, `return_error()` for fatal errors
- `return_error()` will mark the command as failed in the War Room
- Always guard `main()` with the `if __name__` block

---

## test-module Command

Every integration must implement `test-module`. It is called when the user clicks "Test" in the integration configuration UI.

```python
def test_module(client: Client) -> str:
    try:
        client.list_alerts(limit=1)
        return 'ok'
    except DemistoException as e:
        if 'Forbidden' in str(e) or '403' in str(e):
            return 'Authorization Error: make sure API Key is correctly set'
        raise
```

Rules:
- Must return the string `'ok'` on success
- Return a descriptive string (not raise) for expected auth errors
- Raise for unexpected errors so `return_error` in main catches them

---

## Pagination

Use `limit` and `page` args for paginated commands. Use `assign_params` to cleanly build param dicts.

```python
def list_alerts_command(client: Client, args: dict) -> CommandResults:
    limit = arg_to_number(args.get('limit', 50))
    page = arg_to_number(args.get('page', 1))

    response = client.list_alerts(limit=limit, page=page)
    alerts = response.get('data', [])

    return CommandResults(
        outputs_prefix='VendorName.Alert',
        outputs_key_field='id',
        outputs=alerts,
        readable_output=tableToMarkdown('Alerts', alerts, removeNull=True),
        raw_response=response
    )
```

---

## Useful CommonServerPython Helpers

| Helper | Purpose |
|--------|---------|
| `arg_to_number(val)` | Safely converts arg string to int |
| `arg_to_datetime(val)` | Converts arg to datetime object |
| `arg_to_boolean(val)` | Converts "true"/"false" strings to bool |
| `argToList(val)` | Converts comma-separated string to list |
| `assign_params(**kwargs)` | Builds dict, omitting None values |
| `tableToMarkdown(name, data)` | Formats list of dicts as markdown table |
| `removeNull=True` | Pass to `tableToMarkdown` to hide empty columns |
| `DemistoException` | Base exception class — catch for API errors |
| `return_results()` | Output results to War Room |
| `return_error()` | Output error to War Room and mark failed |

---

## Context Path Naming Convention

Context paths must be `PascalCase` and follow: `VendorName.EntityType.FieldName`

Examples:
- `VendorName.Alert.ID`
- `VendorName.Alert.Severity`
- `VendorName.Indicator.Value`

For standard XSOAR entity types (IP, URL, File, Domain), use the standard schemas from `Common.IP`, `Common.URL`, etc. and return `Common.IP` objects via `CommandResults(indicators=...)`.

---

## Fetch Incidents (if required)

If the integration supports "Fetch Incidents":

```python
def fetch_incidents(client: Client, last_run: dict, first_fetch_time: str,
                    max_results: int) -> tuple[dict, list]:
    last_fetch = last_run.get('last_fetch')
    if not last_fetch:
        last_fetch = arg_to_datetime(first_fetch_time).isoformat()

    alerts = client.get_new_alerts(since=last_fetch, limit=max_results)
    incidents = []
    latest_created_time = last_fetch

    for alert in alerts:
        incident_created_time = alert.get('created_at', '')
        incident = {
            'name': f"VendorName Alert: {alert.get('title')}",
            'occurred': incident_created_time,
            'rawJSON': json.dumps(alert),
            'severity': convert_to_demisto_severity(alert.get('severity', 'Low')),
        }
        incidents.append(incident)
        if incident_created_time > latest_created_time:
            latest_created_time = incident_created_time

    next_run = {'last_fetch': latest_created_time}
    return next_run, incidents
```

Severity mapping:
```python
def convert_to_demisto_severity(severity: str) -> int:
    return {
        'low': IncidentSeverity.LOW,       # 1
        'medium': IncidentSeverity.MEDIUM, # 2
        'high': IncidentSeverity.HIGH,     # 3
        'critical': IncidentSeverity.CRITICAL, # 4
    }.get(severity.lower(), IncidentSeverity.UNKNOWN)  # 0
```

In `main()`:
```python
elif command == 'fetch-incidents':
    next_run, incidents = fetch_incidents(
        client=client,
        last_run=demisto.getLastRun(),
        first_fetch_time=params.get('first_fetch', '3 days'),
        max_results=arg_to_number(params.get('max_fetch', 50))
    )
    demisto.setLastRun(next_run)
    demisto.incidents(incidents)
```

---

## Fetch Events (XSIAM event collectors)

If the integration is an event collector (`isfetchevents: true`), it pushes raw events into the
XSIAM dataset `<vendor>_<product>_raw` instead of creating incidents:

```python
VENDOR = 'vendorname'
PRODUCT = 'productname'
DATE_FORMAT = '%Y-%m-%dT%H:%M:%SZ'


def fetch_events(client: Client, last_run: dict, first_fetch_time: str,
                 max_events_per_fetch: int) -> tuple[dict, list]:
    last_fetch = last_run.get('last_fetch')
    if not last_fetch:
        last_fetch = arg_to_datetime(first_fetch_time).strftime(DATE_FORMAT)
    previous_ids = set(last_run.get('ids', []))

    events = client.search_events(since=last_fetch, limit=max_events_per_fetch)
    # Drop events already sent in the previous fetch (boundary-timestamp duplicates)
    events = [e for e in events if e.get('id') not in previous_ids]

    if events:
        last_fetch = events[-1]['created_time']  # events must be in ascending time order
        ids = [e['id'] for e in events if e['created_time'] == last_fetch]
    else:
        ids = list(previous_ids)

    next_run = {'last_fetch': last_fetch, 'ids': ids}
    return next_run, events


def add_time_to_events(events: list):
    for event in events:
        create_time = arg_to_datetime(arg=event.get('created_time'))
        event['_time'] = create_time.strftime(DATE_FORMAT) if create_time else None
```

In `main()`:
```python
elif command == 'fetch-events':
    next_run, events = fetch_events(
        client=client,
        last_run=demisto.getLastRun(),
        first_fetch_time=params.get('first_fetch', '3 days'),
        max_events_per_fetch=arg_to_number(params.get('max_events_per_fetch', 1000)),
    )
    add_time_to_events(events)
    send_events_to_xsiam(events, vendor=VENDOR, product=PRODUCT)
    demisto.setLastRun(next_run)

elif command == 'vendorname-get-events':
    should_push_events = argToBoolean(args.pop('should_push_events'))
    events, results = get_events(client, args)
    return_results(results)
    if should_push_events:
        add_time_to_events(events)
        send_events_to_xsiam(events, vendor=VENDOR, product=PRODUCT)
```

Rules:
- `send_events_to_xsiam()` is provided by CommonServerPython — never hand-roll the push.
- Set `_time` on every event before sending; XSIAM uses it as the event timestamp.
- Request events in ascending time order so the checkpoint is the last element.
- On HTTP 429, send what was collected so far instead of failing the fetch.
- No `CommandResults` context outputs for `fetch-events`; only the manual get-events
  command returns readable output.

---

## File Structure

Every integration lives in its own directory:
```
VendorName/
  VendorName.py        # Python code
  VendorName.yml       # Integration definition (with Python embedded)
  VendorName_test.py   # Unit tests (use pytest + pytest-mock)
  README.md            # Human-readable documentation
```
