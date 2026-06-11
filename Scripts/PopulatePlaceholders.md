# Populate Placeholders

**Author Name:** Kris Bajkowski  
**Platform:** XSOAR & XSIAM  

## Description
This automation script fills in placeholders — it scans an input string (or a dictionary of strings) for `${...}` placeholders and replaces each one with live data pulled from the current incident/issue, its labels, its custom fields, the investigation context, or a JSON object passed directly into the script. The resolved result is written to Context Data so downstream playbook tasks can consume it.

Typical use cases include building dynamic email bodies, notification messages, ticket descriptions, or API payloads inside a playbook without chaining together multiple `Set` and transformer tasks.

The script is platform-aware: it detects whether it is running on XSOAR or XSIAM (`platform == 'x2'`) and resolves `incident.*` placeholders on XSOAR and `issue.*` placeholders on XSIAM accordingly.

## Placeholder Syntax

Placeholders use the format `${path.to.value}`. The path prefix determines where the value is looked up:

| Placeholder Pattern | Source | Platform |
| :--- | :--- | :--- |
| `${incident.labels.<type>}` | The incident label whose `type` matches `<type>`; returns its `value`. | XSOAR only |
| `${incident.<field>}` | The incident field. If not found, automatically retries as `incident.CustomFields.<field>`, so custom fields work without spelling out the `CustomFields` prefix. | XSOAR only |
| `${issue.labels.<type>}` | The issue label whose `type` matches `<type>`; returns its `value`. | XSIAM only |
| `${issue.<field>}` | The issue field, with the same automatic `CustomFields` fallback as above. | XSIAM only |
| `${object.<path>}` | A value from the JSON object passed in the `object` argument. | Both |
| `${<key>}` (key exists in `matchObject`) | A value from the flattened `matchObject` argument — matched **case-insensitively**, by either the bare key name (e.g. `${Region}`) or the full dotted path (e.g. `${SQLResults.Region}`). | Both |
| `${<anything else>}` | Resolved against the investigation Context Data using DT (`demisto.dt`) syntax. | Both |

## Input Arg Requirements

To configure this script properly, set up the following arguments in the script settings:

| Argument | Requirement | Description |
| :--- | :--- | :--- |
| **`inputString`** | *Conditional* | A single string containing `${...}` placeholders to fill in. <br>*Note: Used only if `inputDict` is not provided.* |
| **`inputDict`** | *Conditional* | A JSON object (or JSON string) whose **values** are strings to process in bulk. Each key becomes a context key under the output prefix. <br>*Note: Takes precedence over `inputString` if both are provided.* |
| **`matchObject`** | Optional | A JSON object (or JSON string) used as an additional lookup source. The object is recursively flattened and all keys are lowercased, enabling case-insensitive matching by bare key or dotted path. List items are addressable by index (e.g. `${results.0.name}`). |
| **`object`** | Optional | A JSON object (or JSON string) referenced by `${object.<path>}` placeholders. |
| **`key`** | Optional | The context output prefix. *(Default: `PopulatePlaceholders`)* |
| **`removeNotFound`** | Optional | If set to `yes`, placeholders that cannot be resolved are removed (replaced with an empty string). Otherwise unresolved placeholders are left intact in the output. *(Default: `no`)* |

## Outputs

Results are written to Context Data under the prefix defined by the `key` argument, and a summary table is posted to the War Room.

* **Single string mode (`inputString`):** the completed string is stored directly at the context path `<key>` (e.g. `PopulatePlaceholders`).
* **Dictionary mode (`inputDict`):** each completed value is stored at `<key>.<dictKey>` (e.g. `PopulatePlaceholders.EmailBody`, `PopulatePlaceholders.Subject`).

If the input contains no `${...}` placeholders at all, nothing is written to context and the War Room shows a message noting that no placeholders were found and the script was skipped.

## Examples

**Single string with incident fields and context:**
```
inputString: Ticket ${incident.id} (${incident.severity}) was assigned to ${incident.owner}. IP: ${IP.Address}
```
Result stored at `PopulatePlaceholders`:
```
Ticket 1234 (3) was assigned to kbajkowski. IP: 10.1.2.3
```

**Bulk dictionary with a match object:**
```
inputDict:   {"Subject": "Issue in ${Region}", "Body": "Server ${SQLResults.Hostname} is affected."}
matchObject: {"SQLResults": {"Region": "ASIA", "Hostname": "db-prod-01"}}
```
Results stored at `PopulatePlaceholders.Subject` ("Issue in ASIA") and `PopulatePlaceholders.Body` ("Server db-prod-01 is affected.").

**Explicit object argument:**
```
inputString: User ${object.user.name} logged in from ${object.src_ip}
object:      {"user": {"name": "bob"}, "src_ip": "192.168.1.50"}
```
Result stored at `PopulatePlaceholders`:
```
User bob logged in from 192.168.1.50
```

## Nuances & Important Behavior

* **Platform-specific prefixes:** `incident.*` placeholders are only resolved on XSOAR, and `issue.*` placeholders only on XSIAM. If the "wrong" prefix is used for the platform, the path falls through to a general context lookup, which will usually return nothing. Keep this in mind when sharing playbooks across platforms.
* **Custom fields are automatic:** you can write `${incident.myCustomField}` instead of `${incident.CustomFields.myCustomField}` — the script retries with the `CustomFields` prefix when the direct lookup returns nothing.
* **`matchObject` flattening and key collisions:** every key in `matchObject` is mapped twice — by its bare name and by its full dotted path. If the same bare key name appears at multiple levels of the object, the last one processed wins for the bare-name lookup; use the full dotted path to disambiguate.
* **`matchObject` matching is case-insensitive;** all other lookup types (incident fields, context paths) follow the platform's normal case sensitivity rules.
* **Resolution precedence:** prefixed lookups (`incident.`, `issue.`, `object.`) are evaluated first, then `matchObject`, then the general context. A `matchObject` key therefore cannot override an `incident.*` placeholder.
* **Dictionary mode only outputs modified entries:** in `inputDict` mode, entries whose values contain **no** placeholders are dropped from the output entirely — they are not passed through unchanged. Don't rely on the output dictionary having every input key.
* **Unresolved placeholders are kept by default:** a placeholder that resolves to nothing remains in the text as-is (e.g. `${incident.foo}`), and the entry is still written to context. Set `removeNotFound=yes` to strip them instead.
* **JSON parsing strictness differs by argument:** invalid JSON in `inputDict` or `matchObject` stops the script with an error, but invalid JSON in the `object` argument fails *silently* — `${object.*}` placeholders simply won't resolve.
* **Complex values are serialized:** if a placeholder resolves to a dictionary or list, it is inserted as a JSON string (`json.dumps`); all other values are inserted via `str()`.
* **DT expressions are supported but braces are not:** general context placeholders go through `demisto.dt`, so filter syntax like `${IP(val.Malicious).Address}` works. However, the placeholder regex is non-greedy and terminates at the first `}`, so DT expressions containing a literal `}` will be cut short and fail to resolve.
* **Repeated placeholders:** every occurrence of the same placeholder in the text is replaced, not just the first.
* **Only the current incident/issue is used:** the script operates on the first (current) incident returned by `demisto.incidents()`; it does not look up other incidents.
