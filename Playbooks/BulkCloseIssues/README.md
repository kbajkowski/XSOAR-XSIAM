# Bulk Close Issues

## Overview

`Bulk_Close_Issues_1.1` is a job playbook that searches for alerts/incidents matching a query and closes them in bulk. Some of its behavior — the search query, date range, result limit, close reason/notes, and whether it pauses for a manual confirmation — is driven entirely by a single **JSON List** in XSIAM, so the playbook itself doesn't need to be edited or re-imported to change what it closes. This is useful for environments with remote repository enabled, since pushing to production for minor tweaks can be a headache.

## How it works

1. **Clear Context** – Wipes any existing context so a previous run can't leak into this one.
2. **Get Config** – Reads the JSON List named `Bulk_Close_Issues_Config` (`${lists.Bulk_Close_Issues_Config}`) into context under the key `config`.
3. **Get filtered Issues** – Runs `SearchAlertsV2` using `config.query`, `config.from_date`, and `config.limit` to find the matching alerts.
4. **Is Babysit Mode Enabled?** – Checks `config.babysit_mode`:
   - If `"yes"`, the playbook stops and asks **"Would you like to continue with closure?"** (Yes/No) before doing anything destructive.
   - If anything else (e.g. `"no"`), it skips the confirmation and closes the alerts immediately.
5. **Close Issues** – Calls `closeInvestigation` on every alert returned by the search, using `config.close_reason` and `config.close_notes`.
6. **Close Job** – Closes the job investigation itself once closure is complete (or immediately with "Job cancelled by user" if you answered **No** at the confirmation step).

## Prerequisites: create the config List in XSIAM

The playbook does **not** take inputs — all configuration comes from an XSIAM **List** of type **JSON**.

1. In XSIAM, go to **Automation & Feed Integrations → Lists** (or **Settings → Lists**, depending on your version).
2. Click **New List**.
3. Set the list name to exactly:
   ```
   Bulk_Close_Issues_Config
   ```
   The name must match exactly — the playbook references it as `${lists.Bulk_Close_Issues_Config}`.
4. Set the list type to **JSON**.
5. Paste in the config contents (see [`config.txt`](./config.txt) in this directory for a template) and adjust the values for your use case.
6. Save the list.

### Config fields

| Field | Description | Example |
|---|---|---|
| `query` | The alert search query passed to `SearchAlertsV2`. Use standard alert filter syntax. | `"alert_domain:DOMAIN_SECURITY and -status:0 and name:Akamai"` |
| `close_reason` | The close reason applied to every matched alert. | `"Resolved - Other"` |
| `close_notes` | The close notes applied to every matched alert. | `"Bulk Closed as Part of Go-Live Cleanup"` |
| `from_date` | How far back to search. Accepts relative or absolute dates. | `"365 days ago"` |
| `limit` | Maximum number of alerts to return/close in a single run. | `"500"` |
| `babysit_mode` | `"yes"` to pause for manual confirmation before closing; any other value skips confirmation and closes immediately. | `"yes"` |

**Example list contents:**

```json
{
	"query":"alert_domain:DOMAIN_SECURITY and -status:0 and name:Akamai",
	"close_reason":"Resolved - Other",
	"close_notes":"Bulk Closed as Part of Go-Live Cleanup",
	"from_date":"365 days ago",
	"limit":"500",
	"babysit_mode":"yes"
}
```

## Usage

1. Create or update the `Bulk_Close_Issues_Config` List as described above, with the query and settings for the alerts you want to close.
2. Run the `Bulk_Close_Issues_1.1` playbook (manually, as a job, or on a schedule).
3. If `babysit_mode` is `"yes"`, review the results and reply **Yes** to proceed with closure or **No** to cancel the run without closing anything.
4. Once complete, the job closes itself and the alerts matched by `query` will be closed with the configured `close_reason` and `close_notes`.

## Tips / safety notes

- **Test your query first.** Run the equivalent search in the playground (or via `SearchAlertsV2`) before pointing this playbook at it, to confirm it only matches the alerts you intend to close.
- **Leave `babysit_mode` set to `"yes"`** for any new or unverified query so you get a chance to review the count/scope before the closure actually happens. Only switch it to a non-`"yes"` value (e.g. `"no"`) for queries you've already validated and want to run unattended (e.g. on a schedule).
- **`limit` is a safety cap** as well as a pagination setting — keep it reasonable so a bad query can't close far more alerts than expected in one run.
- Every run reuses the same List, so remember to update `query`/`from_date`/etc. between different bulk-close operations rather than assuming the previous run's settings.
- **Leave Quiet Mode disabled** on the `Get filtered Issues` task (and ideally the playbook run itself). With Quiet Mode off you can open the task and view the `SearchAlertsV2` output directly, letting you verify the alerts your query actually matched — especially useful alongside `babysit_mode` — before closure runs.
