# Nudge Security

## Overview

Nudge Security discovers and manages your organization's SaaS attack surface — every app, account, OAuth grant, app-to-app integration, AI tool, and browser extension in use across the workforce. This integration lets XSOAR/XSIAM search and act on that inventory: find risky OAuth grants and security findings, look up users and their accounts, manage labels and custom fields, monitor AI usage and browser extensions, and kick off employee offboarding playbooks.

## Prerequisites

- A Nudge Security subscription with API access.
- A Nudge Security **API token**. Generate one in the Nudge Security console under **Settings → Integrations → API**. The token is sent as a Bearer token on every request.
- Network access from your XSOAR/XSIAM instance to `https://api.nudgesecurity.io`.

## Configuration

| Parameter | Description | Required |
|-----------|-------------|----------|
| Server URL | Base URL of the Nudge Security API. Default: `https://api.nudgesecurity.io`. | Yes |
| API Token | The Nudge Security API token (Bearer token). | Yes |
| Trust any certificate (not secure) | Skip TLS certificate validation. | No |
| Use system proxy settings | Route requests through the system proxy. | No |

## Searching: filters, search, sorting, and pagination

All `*-search` commands share the same query interface, mirroring the Nudge Security API:

- **filters** — JSON list of conditions combined with **AND**:
  `[{"property": "name", "op": "ilike", "value": "%slack%"}, {"property": "is_ignored", "op": "=", "value": false}]`
- **search** — JSON list of conditions combined with **OR** (same condition format).
- **Operators:** `=`, `!=`, `<`, `<=`, `>`, `>=`, `like`, `ilike`, `not_like`, `not_ilike`, `in`, `notin`, `notnull`, `isnull`.
- **Pagination:** `page` (default 1) and `per_page` (default 50, max 100). Search results include the page metadata in the readable output (`page X of Y, Z total`).
- **Sorting:** `sort_by` (entity-specific property) and `sort_direction` (`asc`/`desc`).

The supported filter properties for each command are listed in the command's `filters` argument description in the UI and below.

---

## Commands

### Apps

#### nudge-app-search
**Description:** Searches for SaaS apps discovered by Nudge Security.

**Arguments:**
| Argument | Description | Required | Default |
|----------|-------------|----------|---------|
| filters | JSON list of AND conditions. Properties: id, name, domain_canonical, account_count, adoption_percentage, first_date, fields, service_info.name, technical_contact_id, technical_contact.name, category, is_ignored | No | |
| search | JSON list of OR conditions (same format) | No | |
| page | Page number | No | 1 |
| per_page | Results per page (max 100) | No | 50 |
| sort_by | id, name, domain_canonical, account_count, adoption_percentage, first_date | No | |
| sort_direction | asc / desc | No | asc |

**Context Output:**
| Path | Type | Description |
|------|------|-------------|
| Nudge.App.id | Number | Unique app ID |
| Nudge.App.name | String | App name |
| Nudge.App.domain_canonical | String | Canonical domain |
| Nudge.App.category | String | App category |
| Nudge.App.account_count | Number | Number of discovered accounts |
| Nudge.App.adoption_percentage | Number | Accounts active in last 90 days (%) |
| Nudge.App.first_date | Date | First discovery date |
| Nudge.App.is_ignored | Boolean | Whether the app is ignored |
| Nudge.App.service_info | Unknown | Vendor service information |

**Example:**
`!nudge-app-search filters="[{\"property\": \"category\", \"op\": \"=\", \"value\": \"AI Tools\"}]" sort_by=account_count sort_direction=desc`

#### nudge-app-supply-chain-search
**Description:** Searches for apps in your SaaS supply chain by service category. Same arguments and outputs as `nudge-app-search`, plus:

| Argument | Description | Required |
|----------|-------------|----------|
| category | Service category (Finance, HR, Security, AI Tools, ...) | Yes |

**Example:**
`!nudge-app-supply-chain-search category="AI Tools"`

#### nudge-app-get
**Description:** Retrieves a single app by ID.

| Argument | Description | Required |
|----------|-------------|----------|
| app_id | Unique app ID | Yes |

**Context Output:** Same `Nudge.App` paths as `nudge-app-search`.

**Example:** `!nudge-app-get app_id=12345`

#### nudge-app-category-set
**Description:** Sets the category of an app.

| Argument | Description | Required |
|----------|-------------|----------|
| app_id | Unique app ID | Yes |
| category | One of the predefined Nudge categories | Yes |

**Example:** `!nudge-app-category-set app_id=12345 category="Developer Tools"`

#### nudge-app-field-set / nudge-app-field-delete
**Description:** Sets or deletes a custom field value on an app.

| Argument | Description | Required |
|----------|-------------|----------|
| app_id | Unique app ID | Yes |
| field_id | Custom field ID | Yes |
| value | Value to set (set: required; delete: only needed for MULTI_SELECT fields) | Set: Yes / Delete: No |

**Context Output (set):** `Nudge.AppField.id`, `Nudge.AppField.name`, `Nudge.AppField.value`

**Example:** `!nudge-app-field-set app_id=12345 field_id=7 value="Approved"`

#### nudge-app-label-add / nudge-app-label-delete
**Description:** Adds or deletes a label on an app. The label must already exist (`nudge-label-create`).

| Argument | Description | Required |
|----------|-------------|----------|
| app_id | Unique app ID | Yes |
| value | Label value | Yes |

**Example:** `!nudge-app-label-add app_id=12345 value="sanctioned"`

#### nudge-app-instance-search
**Description:** Searches for instances (tenants/workspaces) of a specific app. Standard search arguments plus:

| Argument | Description | Required |
|----------|-------------|----------|
| app_id | App whose instances to search | Yes |

**Context Output:** `Nudge.AppInstance.*` (id, name, display_name, domain_canonical, identifier, connection_status, sso_label, first_date, saas_id, technical_contact_id)

**Example:** `!nudge-app-instance-search app_id=12345`

#### nudge-app-technical-contact-set / nudge-app-technical-contact-delete
**Description:** Sets or removes the technical contact of an app.

| Argument | Description | Required |
|----------|-------------|----------|
| app_id | Unique app ID | Yes |
| user_id | User to set as technical contact (set only) | Yes (set) |

**Example:** `!nudge-app-technical-contact-set app_id=12345 user_id=678`

### Accounts

#### nudge-account-search
**Description:** Searches for SaaS accounts. Standard search arguments. Filter properties: id, first_date, last_date, name, user_id, domain_canonical, mfa_status, fields, metadata.user_email, app_id, app.is_ignored. Sort: id, first_date, last_date.

**Context Output:**
| Path | Type | Description |
|------|------|-------------|
| Nudge.Account.id | Number | Unique account ID |
| Nudge.Account.name | String | Account name (email/username) |
| Nudge.Account.domain_canonical | String | App domain |
| Nudge.Account.app_id | Number | Owning app ID |
| Nudge.Account.user_id | Number | Owning user ID |
| Nudge.Account.mfa_status | String | MFA status |
| Nudge.Account.is_admin | Boolean | Admin privileges |
| Nudge.Account.first_date | Date | First discovery date |
| Nudge.Account.last_date | Date | Most recent activity |
| Nudge.Account.auth_methods | Unknown | Observed authentication methods |

**Example:**
`!nudge-account-search filters="[{\"property\": \"mfa_status\", \"op\": \"=\", \"value\": \"disabled\"}]"`

#### nudge-account-get
**Description:** Retrieves a single account by ID. Argument: `account_id` (required). Same `Nudge.Account` outputs.

**Example:** `!nudge-account-get account_id=9876`

#### nudge-account-field-set / nudge-account-field-delete
**Description:** Sets or deletes a custom field value on an account. Arguments: `account_id` (required), `field_id` (required), `value` (set: required; delete: MULTI_SELECT only).

**Context Output (set):** `Nudge.AccountField.id`, `Nudge.AccountField.name`, `Nudge.AccountField.value`

#### nudge-account-label-add / nudge-account-label-delete
**Description:** Adds or deletes a label on an account. Arguments: `account_id` (required), `value` (required).

### OAuth Grants

#### nudge-oauth-grant-search
**Description:** Searches for OAuth grants. Standard search arguments. Filter properties: id, first_seen, last_seen, risk_score, name, oauth_integration, risk_level, user_id, fields, access_type, parent_account_id, account_id, app.is_ignored, account_category, permissions, user_account_status, user_is_admin, org_unit_name. Sort: id, first_seen, last_seen, risk_score.

**Context Output:**
| Path | Type | Description |
|------|------|-------------|
| Nudge.OAuthGrant.id | Number | Unique grant ID |
| Nudge.OAuthGrant.name | String | Application granted access |
| Nudge.OAuthGrant.risk_level | String | Risk level |
| Nudge.OAuthGrant.risk_score | Number | Risk score |
| Nudge.OAuthGrant.user_id | Number | Granting user ID |
| Nudge.OAuthGrant.account_id | Number | Associated account ID |
| Nudge.OAuthGrant.oauth_integration | Boolean | Is app-to-app integration |
| Nudge.OAuthGrant.first_seen | Date | First seen |
| Nudge.OAuthGrant.last_seen | Date | Last seen |
| Nudge.OAuthGrant.scopes | Unknown | Granted OAuth scopes |
| Nudge.OAuthGrant.insights | Unknown | Risk insights |

**Example:**
`!nudge-oauth-grant-search filters="[{\"property\": \"risk_level\", \"op\": \"=\", \"value\": \"high\"}]" sort_by=risk_score sort_direction=desc`

#### nudge-oauth-grant-get
**Description:** Retrieves a single OAuth grant by ID. Argument: `oauth_id` (required). Same `Nudge.OAuthGrant` outputs.

### Events

#### nudge-event-search
**Description:** Searches discovery/activity events. Standard search arguments plus optional `start_date`/`end_date` convenience arguments (ISO 8601 or relative, e.g., "7 days ago") that filter on the event date. Filter properties: id, date, type, user_id, from_email, user_email, domain_canonical, account_id. Sort: id, date, type.

**Context Output:**
| Path | Type | Description |
|------|------|-------------|
| Nudge.Event.id | Number | Unique event ID |
| Nudge.Event.event_id | String | External event identifier |
| Nudge.Event.type | String | Event type |
| Nudge.Event.date | Date | Event date |
| Nudge.Event.user_email | String | Associated user email |
| Nudge.Event.from_email | String | Sender email |
| Nudge.Event.domain_canonical | String | Associated app domain |
| Nudge.Event.account_id | Number | Associated account ID |
| Nudge.Event.resources | Unknown | Attached resources |

**Example:**
`!nudge-event-search start_date="7 days ago" filters="[{\"property\": \"type\", \"op\": \"=\", \"value\": \"new_app\"}]" sort_by=date sort_direction=desc`

#### nudge-event-get
**Description:** Retrieves a single event by ID. Argument: `event_id` (required). Same `Nudge.Event` outputs.

### Users

#### nudge-user-search
**Description:** Searches for users (employees). Standard search arguments. Filter properties: id, name, primary_email, external_user_id, status, user_email. Sort: id, name.

**Context Output:**
| Path | Type | Description |
|------|------|-------------|
| Nudge.User.id | Number | Unique user ID |
| Nudge.User.name | String | Full name |
| Nudge.User.primary_email | String | Primary email |
| Nudge.User.status | String | User status |
| Nudge.User.is_admin | Boolean | Is admin |
| Nudge.User.has_2fa | Boolean | Has 2FA enabled |
| Nudge.User.creation_time | Date | Creation date |
| Nudge.User.in_high_risk_country | Boolean | Recent activity from high-risk country |
| Nudge.User.org_unit | Unknown | Organizational unit |

**Example:**
`!nudge-user-search search="[{\"property\": \"primary_email\", \"op\": \"ilike\", \"value\": \"%jdoe%\"}]"`

#### nudge-user-get
**Description:** Retrieves a single user by ID. Argument: `user_id` (required). Same `Nudge.User` outputs plus recovery_email/recovery_phone.

### Groups

#### nudge-group-search
**Description:** Searches for user groups. Standard search arguments. Filter properties: id, risk_level_value, creation_date, external_id, counters.total_members, counters.total_saas_accounts, counters.total_apps_introduced, user_group_metadata.visibility, user_group_metadata.group_type, user_group_metadata.who_can_manage_members, user_group_metadata.who_can_join, user_group_metadata.who_can_view_messages, user_group_metadata.admin_created. Sort: id, risk_level_value, creation_date.

**Context Output:** `Nudge.Group.*` (id, name, external_id, description, risk_level, risk_level_value, creation_date, counters, user_group_metadata)

#### nudge-group-get
**Description:** Retrieves a single group by ID. Argument: `group_id` (required). Same `Nudge.Group` outputs.

#### nudge-group-member-search
**Description:** Searches members of a group. Standard search arguments plus `group_id` (required). Filter properties: id, member_role, user.name, user.primary_email, user.external_user_id, user.status.

**Context Output:** `Nudge.GroupMember.id`, `Nudge.GroupMember.member_role`, `Nudge.GroupMember.user` (full user object)

**Example:** `!nudge-group-member-search group_id=42`

### Notifications

#### nudge-notification-search
**Description:** Searches notifications generated by Nudge notification rules. Standard search arguments. Filter properties: id, creation_date, notification_rule_id, user_id, status, target_app_id, target_account_id, target_oauth_grant_id, target_aws_account_id, target_event_id, target_resource_id. Sort: id, creation_date.

**Context Output:** `Nudge.Notification.*` (id, summary, status, creation_date, target_app_id, target_account_id, target_aws_account_id, target_event_id, target_oauth_grant_id, target_resource_id)

#### nudge-notification-get
**Description:** Retrieves a single notification by ID, including its `details`. Argument: `notification_id` (required).

### Findings

#### nudge-finding-search
**Description:** Searches security posture findings. Standard search arguments. Filter properties: id, result, status, creation_time, last_check_time, resolution_time, reopen_time, description, finding_rule_id, app_integration_id, resource_id, resource_type, resource_type_name, default_resolution_owner_id, resolution_owner_id, risk_category.risk_category, severity.risk_severity. Sort: id, result, status, creation_time, last_check_time, resolution_time, reopen_time.

**Context Output:**
| Path | Type | Description |
|------|------|-------------|
| Nudge.Finding.id | Number | Unique finding ID |
| Nudge.Finding.status | String | Finding status |
| Nudge.Finding.result | String | Check result |
| Nudge.Finding.description | String | Description |
| Nudge.Finding.creation_time | Date | Creation date |
| Nudge.Finding.resource_type_name | String | Resource type display name |
| Nudge.Finding.resource_id | Number | Resource ID |
| Nudge.Finding.finding_rule | Unknown | Rule (name, severity, risk category) |
| Nudge.Finding.resolution_owner | Unknown | Responsible user |

**Example:**
`!nudge-finding-search filters="[{\"property\": \"status\", \"op\": \"=\", \"value\": \"open\"}]"`

#### nudge-finding-get
**Description:** Retrieves a single finding by ID. Argument: `finding_id` (required). Same `Nudge.Finding` outputs.

### Custom Fields

#### nudge-field-create
**Description:** Creates a custom field for apps and/or accounts.

| Argument | Description | Required |
|----------|-------------|----------|
| name | Field name | Yes |
| field_type | SELECT, MULTI_SELECT, DATE_TIME, NUMERIC, TEXT | Yes |
| scopes | Comma-separated: app, account | Yes |

**Context Output:** `Nudge.Field.*` (id, name, field_type, scopes, system_defined, allowed_values)

**Example:** `!nudge-field-create name="Review Status" field_type=SELECT scopes=app`

#### nudge-field-search
**Description:** Searches custom fields. Standard search arguments. Filter properties: id, name, field_type, system_defined.

#### nudge-field-get
**Description:** Retrieves a field by ID. Argument: `field_id` (required).

#### nudge-field-update
**Description:** Updates a field's name and/or scopes. Arguments: `field_id` (required), `name`, `scopes`.

#### nudge-field-delete
**Description:** Deletes a field definition (removes it from all entities). Argument: `field_id` (required).

#### nudge-field-allowed-value-add / nudge-field-allowed-value-update / nudge-field-allowed-value-delete
**Description:** Manages allowed values of SELECT/MULTI_SELECT fields.

| Argument | Description | Required |
|----------|-------------|----------|
| field_id | Field ID | Yes |
| value | The allowed value (existing value for update/delete) | Yes |
| new_value | Replacement value (update only) | No |
| color / background_color / text_color | Chip styling in the Nudge UI | No |

**Context Output (add/update):** `Nudge.FieldAllowedValue.*` (value, color, background_color, text_color)

### Labels

#### nudge-label-create / nudge-label-update / nudge-label-delete / nudge-label-search
**Description:** Manages labels that can be attached to apps, accounts, and OAuth grants.

| Argument | Description | Required |
|----------|-------------|----------|
| value | Label value (existing value for update/delete) | Yes |
| new_value | Replacement value (update only) | No |
| color / background_color / text_color | Chip styling in the Nudge UI | No |

Search supports the standard search arguments (filter property: value).

**Context Output (create/update/search):** `Nudge.Label.value`, `Nudge.Label.color`, `Nudge.Label.system_defined`

**Example:** `!nudge-label-create value="sanctioned" color="#00AA00"`

### App-to-App Integrations

#### nudge-app-integration-search
**Description:** Searches app-to-app integrations (machine identities). Standard search arguments. Filter properties: id, first_date, last_date, risk_score, name, risk_level, created_by_user_id, status, auth_type, sources, authorizing_app_id, app_id, instance. Sort: id, first_date, last_date, risk_score.

**Context Output:** `Nudge.AppIntegration.*` (id, name, auth_type, auth_method_name, status, risk_level, risk_score, app_id, authorizing_app_id, instance_id, created_by_user_id, mfa_status, first_date, last_date, scopes, insights, sources)

#### nudge-app-integration-get
**Description:** Retrieves a single app-to-app integration by its authentication method ID. Argument: `auth_method_id` (required).

### App Instances

#### nudge-instance-search
**Description:** Searches app instances across all apps. Standard search arguments. Filter properties: id, display_name, domain_canonical, first_date, identifier, name, sso_label, external_id, saas_id, origins, technical_contact_id, technical_contact_origin. Sort: id, display_name, domain_canonical, first_date.

**Context Output:** `Nudge.AppInstance.*` (id, name, display_name, domain_canonical, identifier, external_id, connection_status, sso_label, first_date, app_id, technical_contact_id, counters)

#### nudge-instance-get
**Description:** Retrieves a single app instance by ID. Argument: `instance_id` (required).

### AI Usage

#### nudge-ai-session-search
**Description:** Searches AI tool usage sessions. **The API requires a date range**, so `start_date` and `end_date` are required (ISO 8601 or relative, e.g., "7 days ago" / "now"). Additional filter properties: start_date, finish_date, service_domain, user_id, saas_id, identifier, data_insight_categories, data_activity_types.

**Context Output:** `Nudge.AiSession.*` (identifier, user_id, saas_id, service_domain, start_date, finish_date, query_count, data_insight_categories, data_activity_types)

**Example:** `!nudge-ai-session-search start_date="30 days ago" end_date="now"`

#### nudge-ai-prompt-search
**Description:** Searches individual AI prompts. **The API requires a date range**, so `start_date` and `end_date` are required (filters on the prompt submission date). Additional filter properties: id, submission_date, ai_session_start_date, user_id, ai_session_identifier, data_insight_categories, data_activity_types, data_insight_types, data_insight_subtypes.

**Context Output:** `Nudge.AiPrompt.*` (id, user_id, prompt_query, submission_date, ai_session_identifier, ai_session_start_date, data_insight_categories, data_activity_types)

**Example:** `!nudge-ai-prompt-search start_date="7 days ago" end_date="now" filters="[{\"property\": \"user_id\", \"op\": \"=\", \"value\": 678}]"`

### Browser Extensions

#### nudge-browser-extension-client-search
**Description:** Searches devices/browsers running the Nudge Security browser extension. Standard search arguments. Filter properties: id, guid, last_heartbeat, version, registration_status, user_id, browser, browser_family, browser_version, os, os_family, os_version, device_identifier, device_type, device_os, hostname, extension_id, user_agent, storage_usage.

**Context Output:** `Nudge.BrowserExtensionClient.*` (id, guid, hostname, browser, browser_version, os, user_id, registration_status, last_heartbeat, device_identifier, device_type, version)

#### nudge-browser-extension-record-search
**Description:** Searches third-party browser extensions inventoried across the workforce. Standard search arguments. Filter properties: id, status, deployment_type, first_date, last_date, version, browser_extension.identifier, browser_extension.browser.

**Context Output:** `Nudge.BrowserExtensionRecord.*` (id, status, version, deployment_type, first_date, last_date, browser_extension_client_id, browser_extension, permissions, host_permissions)

### Offboarding

#### nudge-offboarding-start
**Description:** Starts the Nudge Security offboarding playbook for a user (revokes sessions, surfaces accounts to transfer/close, etc.). Returns a URL to track progress.

| Argument | Description | Required |
|----------|-------------|----------|
| user_id | User to offboard | Yes |

**Context Output:** `Nudge.Offboarding.user_id`, `Nudge.Offboarding.url`

**Example:** `!nudge-offboarding-start user_id=678`

---

## Incident Fetching

This integration does not fetch incidents. Use `nudge-event-search`, `nudge-finding-search`, or `nudge-notification-search` in scheduled playbooks/jobs if you need to poll for new activity.

## Troubleshooting

| Symptom | Likely cause / fix |
|---------|--------------------|
| `Authorization Error: make sure the API Token is correctly set` on Test | The API token is missing, expired, or revoked. Generate a new token in the Nudge Security console and update the instance configuration. |
| `401 Unauthorized` on commands | Same as above — the Bearer token was rejected. |
| `400` validation errors on search commands | Malformed `filters`/`search` JSON, an unsupported `property` for that entity, or an invalid `op`. Check the argument description for the supported property list. The AI search commands also return 400 if the required date range is missing. |
| `404 Not Found` on get commands | The entity ID does not exist in your organization. |
| Empty results with `like`/`ilike` filters | These operators require SQL-style wildcards — wrap the value in `%`, e.g., `"%slack%"`. |
| SSL certificate errors | If you are behind a TLS-inspecting proxy, either install the proxy CA or enable **Trust any certificate** (not recommended for production). |
| Results capped at 100 | `per_page` maxes out at 100 — paginate with the `page` argument; total pages are shown in the readable output. |
