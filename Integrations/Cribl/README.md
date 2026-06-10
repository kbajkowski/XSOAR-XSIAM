# Cribl API

## Overview

This integration connects XSOAR/XSIAM to the Cribl REST API (v4.18), enabling analysts and operators to monitor and manage Cribl Stream and Edge deployments directly from playbooks and the War Room. It covers system health, worker groups, worker nodes, pipelines, sources, destinations, jobs, lookup files, and system metrics.

## Prerequisites

This integration uses OAuth2 client credentials to authenticate with the Cribl API.

**Cribl.Cloud:**
1. Log in to your Cribl.Cloud organization.
2. Navigate to **Settings > Global Settings > API Authentication**.
3. Create a new client and note the **Client ID** and **Client Secret**.
4. Assign the appropriate roles: read-only use requires at minimum the `read` role; write operations (deploy, restart, cancel/pause/resume jobs) require admin or operator roles.

**On-Premises / Self-Hosted:**
- If your on-prem deployment has an OAuth2 identity provider configured, obtain a Client ID and Client Secret from it and supply the token endpoint URL in the **Token URL** parameter.
- Otherwise, configure an API token under **Settings > Global Settings > API Monitoring** and contact Cribl support for details on client credentials configuration.

## Configuration

| Parameter | Description | Required |
|-----------|-------------|----------|
| Server URL | Base URL for the Cribl API, e.g. `https://main-<org>.cribl.cloud/api/v1`. Worker Group and Worker Node routing is handled automatically by each command — you do not need to include `/m/{groupName}` or `/w/{nodeId}` here. | Yes |
| Client ID | OAuth2 client ID from Cribl.Cloud API Authentication settings. | Yes |
| Client Secret | OAuth2 client secret. | Yes |
| Token URL | OAuth2 token endpoint. Defaults to `https://login.cribl.cloud/oauth/token`. Override for on-premises deployments with a custom identity provider. | No |
| Trust any certificate (not secure) | Disable SSL certificate verification. Use only in lab environments. | No |
| Use system proxy settings | Route API requests through the system proxy. | No |

## Commands

### criblapi-get-system-info

**Description:** Get basic system information for the current Cribl instance.

**Arguments:**

| Argument | Description | Required |
|----------|-------------|----------|
| fields | Comma-separated list of SystemInfoField values to include. | No |
| messages | If `true`, include system messages. | No |
| conf | If `true`, include a configuration summary. | No |

**Context Output:**

| Path | Type | Description |
|------|------|-------------|
| CriblAPI.SystemInfo.guid | String | Unique identifier of the instance |
| CriblAPI.SystemInfo.version | String | Cribl product version |
| CriblAPI.SystemInfo.hostname | String | Hostname |
| CriblAPI.SystemInfo.product | String | Product name (stream, edge) |

**Example:** `!criblapi-get-system-info`

---

### criblapi-get-health

**Description:** Get the current health status of the Cribl server.

**Arguments:** None

**Context Output:**

| Path | Type | Description |
|------|------|-------------|
| CriblAPI.Health.status | String | Overall health status |
| CriblAPI.Health.uptime | Number | Server uptime in seconds |
| CriblAPI.Health.mode | String | Server mode (primary, standby) |

**Example:** `!criblapi-get-health`

---

### criblapi-list-worker-groups

**Description:** List all Worker Groups, Outpost Groups, or Edge Fleets.

**Arguments:**

| Argument | Description | Required | Default |
|----------|-------------|----------|---------|
| product | Cribl product (stream, edge, outpost) | No | stream |
| fields | Additional fields (git.commit, git.localChanges, git.log) | No | |

**Context Output:**

| Path | Type | Description |
|------|------|-------------|
| CriblAPI.WorkerGroup.id | String | Group ID |
| CriblAPI.WorkerGroup.name | String | Display name |
| CriblAPI.WorkerGroup.workerCount | Number | Connected worker count |
| CriblAPI.WorkerGroup.configVersion | String | Deployed config version |

**Example:** `!criblapi-list-worker-groups product=stream`

---

### criblapi-get-worker-group

**Description:** Get details for a specific Worker Group.

**Arguments:**

| Argument | Description | Required | Default |
|----------|-------------|----------|---------|
| id | Worker Group ID | Yes | |
| product | Cribl product | No | stream |
| fields | Additional fields to include | No | |

**Example:** `!criblapi-get-worker-group id="default"`

---

### criblapi-deploy-worker-group

**Description:** Deploy the latest committed configuration to a Worker Group.

**Arguments:**

| Argument | Description | Required | Default |
|----------|-------------|----------|---------|
| id | Worker Group ID | Yes | |
| product | Cribl product | No | stream |

**Example:** `!criblapi-deploy-worker-group id="default" product=stream`

---

### criblapi-list-workers

**Description:** Get detailed metadata for Worker, Edge, or Outpost Nodes.

**Arguments:**

| Argument | Description | Required | Default |
|----------|-------------|----------|---------|
| product | Cribl product | No | stream |
| limit | Maximum nodes to return | No | |
| offset | Pagination offset | No | |
| filter_exp | Filter expression | No | |

**Context Output:**

| Path | Type | Description |
|------|------|-------------|
| CriblAPI.Worker.guid | String | Worker GUID |
| CriblAPI.Worker.hostname | String | Hostname |
| CriblAPI.Worker.group | String | Worker Group |
| CriblAPI.Worker.status | String | Connection status |
| CriblAPI.Worker.version | String | Cribl version |

**Example:** `!criblapi-list-workers product=stream limit=20`

---

### criblapi-restart-workers

**Description:** Restart all Worker Nodes for the specified product.

**Arguments:**

| Argument | Description | Required | Default |
|----------|-------------|----------|---------|
| product | Cribl product | No | stream |

**Example:** `!criblapi-restart-workers product=stream`

---

### criblapi-list-pipelines

**Description:** List all Pipelines. By default queries the Leader context. Use `worker_group` or `worker_node` to scope to a specific Worker Group or Worker Node.

**Arguments:**

| Argument | Description | Required |
|----------|-------------|----------|
| worker_group | Worker Group ID to scope the request (e.g., `default`). Omit to query the Leader. | No |
| worker_node | Worker Node ID to scope the request. Takes precedence over `worker_group` if both are provided. | No |

**Context Output:**

| Path | Type | Description |
|------|------|-------------|
| CriblAPI.Pipeline.id | String | Pipeline ID |
| CriblAPI.Pipeline.description | String | Description |
| CriblAPI.Pipeline.functions | Unknown | Pipeline functions |

**Example:** `!criblapi-list-pipelines worker_group="default"`

---

### criblapi-get-pipeline

**Description:** Get details for a specific Pipeline. Use `worker_group` or `worker_node` to scope to a specific context.

**Arguments:**

| Argument | Description | Required |
|----------|-------------|----------|
| id | Pipeline ID | Yes |
| worker_group | Worker Group ID to scope the request. Omit to query the Leader. | No |
| worker_node | Worker Node ID to scope the request. Takes precedence over `worker_group`. | No |

**Example:** `!criblapi-get-pipeline id="my-pipeline" worker_group="default"`

---

### criblapi-list-sources

**Description:** List all Sources (inputs). Use `worker_group` or `worker_node` to scope to a specific Worker Group or Worker Node.

**Arguments:**

| Argument | Description | Required |
|----------|-------------|----------|
| type | Filter by source type (e.g., syslog, http, kafka) | No |
| worker_group | Worker Group ID to scope the request (e.g., `default`). Omit to query the Leader. | No |
| worker_node | Worker Node ID to scope the request. Takes precedence over `worker_group`. | No |

**Context Output:**

| Path | Type | Description |
|------|------|-------------|
| CriblAPI.Source.id | String | Source ID |
| CriblAPI.Source.type | String | Source type |
| CriblAPI.Source.disabled | Boolean | Whether disabled |
| CriblAPI.Source.pipeline | String | Attached pipeline |

**Example:** `!criblapi-list-sources type=syslog worker_group="default"`

---

### criblapi-get-source

**Description:** Get details for a specific Source. Use `worker_group` or `worker_node` to scope to the correct context.

**Arguments:**

| Argument | Description | Required |
|----------|-------------|----------|
| id | Source ID | Yes |
| worker_group | Worker Group ID to scope the request. Omit to query the Leader. | No |
| worker_node | Worker Node ID to scope the request. Takes precedence over `worker_group`. | No |

**Example:** `!criblapi-get-source id="my-syslog-source" worker_group="default"`

---

### criblapi-list-source-status

**Description:** List status and optional metrics for all Sources. Use `worker_group` or `worker_node` to scope to the correct context.

**Arguments:**

| Argument | Description | Required |
|----------|-------------|----------|
| metrics | Include metrics (true/false) | No |
| limit | Maximum items to return | No |
| offset | Pagination offset | No |
| worker_group | Worker Group ID to scope the request. Omit to query the Leader. | No |
| worker_node | Worker Node ID to scope the request. Takes precedence over `worker_group`. | No |

**Example:** `!criblapi-list-source-status metrics=true worker_group="default"`

---

### criblapi-get-source-status

**Description:** Get status and optional metrics for a specific Source. Use `worker_group` or `worker_node` to scope to the correct context.

**Arguments:**

| Argument | Description | Required |
|----------|-------------|----------|
| id | Source ID | Yes |
| metrics | Include metrics (true/false) | No |
| worker_group | Worker Group ID to scope the request. Omit to query the Leader. | No |
| worker_node | Worker Node ID to scope the request. Takes precedence over `worker_group`. | No |

**Example:** `!criblapi-get-source-status id="my-source" metrics=true worker_group="default"`

---

### criblapi-list-destinations

**Description:** List all Destinations (outputs). Use `worker_group` or `worker_node` to scope to a specific Worker Group or Worker Node.

**Arguments:**

| Argument | Description | Required |
|----------|-------------|----------|
| type | Filter by destination type (e.g., splunk, s3, kafka) | No |
| worker_group | Worker Group ID to scope the request (e.g., `default`). Omit to query the Leader. | No |
| worker_node | Worker Node ID to scope the request. Takes precedence over `worker_group`. | No |

**Context Output:**

| Path | Type | Description |
|------|------|-------------|
| CriblAPI.Destination.id | String | Destination ID |
| CriblAPI.Destination.type | String | Destination type |
| CriblAPI.Destination.disabled | Boolean | Whether disabled |

**Example:** `!criblapi-list-destinations worker_group="default"`

---

### criblapi-get-destination

**Description:** Get details for a specific Destination. Use `worker_group` or `worker_node` to scope to the correct context.

**Arguments:**

| Argument | Description | Required |
|----------|-------------|----------|
| id | Destination ID | Yes |
| worker_group | Worker Group ID to scope the request. Omit to query the Leader. | No |
| worker_node | Worker Node ID to scope the request. Takes precedence over `worker_group`. | No |

**Example:** `!criblapi-get-destination id="my-splunk-out" worker_group="default"`

---

### criblapi-list-destination-status

**Description:** List status and optional metrics for all Destinations. Use `worker_group` or `worker_node` to scope to the correct context.

**Arguments:**

| Argument | Description | Required |
|----------|-------------|----------|
| metrics | Include metrics (true/false) | No |
| limit | Maximum items to return | No |
| offset | Pagination offset | No |
| worker_group | Worker Group ID to scope the request. Omit to query the Leader. | No |
| worker_node | Worker Node ID to scope the request. Takes precedence over `worker_group`. | No |

**Example:** `!criblapi-list-destination-status metrics=true worker_group="default"`

---

### criblapi-get-destination-status

**Description:** Get status and optional metrics for a specific Destination. Use `worker_group` or `worker_node` to scope to the correct context.

**Arguments:**

| Argument | Description | Required |
|----------|-------------|----------|
| id | Destination ID | Yes |
| metrics | Include metrics (true/false) | No |
| worker_group | Worker Group ID to scope the request. Omit to query the Leader. | No |
| worker_node | Worker Node ID to scope the request. Takes precedence over `worker_group`. | No |

**Example:** `!criblapi-get-destination-status id="my-dest" metrics=true worker_group="default"`

---

### criblapi-list-jobs

**Description:** List all jobs, with optional filtering.

**Arguments:**

| Argument | Description | Required |
|----------|-------------|----------|
| limit | Maximum jobs to return | No |
| offset | Pagination offset | No |
| run_type | Filter by run type | No |
| state | Filter by state (e.g., running, completed, failed) | No |
| collector_id | Filter by collector ID | No |

**Context Output:**

| Path | Type | Description |
|------|------|-------------|
| CriblAPI.Job.id | String | Job instance ID |
| CriblAPI.Job.type | String | Job type |
| CriblAPI.Job.status | String | Current status |
| CriblAPI.Job.startTime | Date | Start timestamp |
| CriblAPI.Job.numEvents | Number | Events processed |

**Example:** `!criblapi-list-jobs state=running limit=50`

---

### criblapi-get-job

**Description:** Get details for a specific job by instance ID.

**Arguments:**

| Argument | Description | Required |
|----------|-------------|----------|
| id | Job instance ID | Yes |

**Example:** `!criblapi-get-job id="1608713335.3"`

---

### criblapi-cancel-job

**Description:** Cancel a running job.

**Arguments:**

| Argument | Description | Required |
|----------|-------------|----------|
| id | Job instance ID | Yes |

**Example:** `!criblapi-cancel-job id="1608713335.3"`

---

### criblapi-pause-job

**Description:** Pause a running job.

**Arguments:**

| Argument | Description | Required |
|----------|-------------|----------|
| id | Job instance ID | Yes |

**Example:** `!criblapi-pause-job id="1608713335.3"`

---

### criblapi-resume-job

**Description:** Resume a paused job.

**Arguments:**

| Argument | Description | Required |
|----------|-------------|----------|
| id | Job instance ID | Yes |

**Example:** `!criblapi-resume-job id="1608713335.3"`

---

### criblapi-list-lookups

**Description:** List all Lookup files.

**Arguments:** None

**Context Output:**

| Path | Type | Description |
|------|------|-------------|
| CriblAPI.Lookup.id | String | Lookup ID |
| CriblAPI.Lookup.description | String | Description |
| CriblAPI.Lookup.fileName | String | Filename |
| CriblAPI.Lookup.size | Number | File size in bytes |

**Example:** `!criblapi-list-lookups`

---

### criblapi-get-lookup

**Description:** Get details for a specific Lookup file.

**Arguments:**

| Argument | Description | Required |
|----------|-------------|----------|
| id | Lookup ID | Yes |

**Example:** `!criblapi-get-lookup id="geo-data"`

---

### criblapi-query-metrics

**Description:** Query and aggregate internal system metrics.

**Arguments:**

| Argument | Description | Required |
|----------|-------------|----------|
| filter_expr | Filter expression for metric selection | No |
| pipeline | Aggregation pipeline expression | No |
| earliest | Start of time range (e.g., -15m, -1h, epoch) | No |
| latest | End of time range (e.g., now, epoch) | No |
| num_buckets | Number of time buckets for aggregation | No |

**Context Output:**

| Path | Type | Description |
|------|------|-------------|
| CriblAPI.Metrics | Unknown | Aggregated metric results |

**Example:** `!criblapi-query-metrics filter_expr="cribl.logstream.inputs.in_bytes" earliest="-15m" latest="now"`

---

## Troubleshooting

**Authorization Error on Test:**
- Verify the Client ID and Client Secret are correct. These are created under **Settings > Global Settings > API Authentication** in your Cribl.Cloud organization.
- If using a custom Token URL for on-prem, confirm the endpoint is reachable from the XSOAR/XSIAM server.

**401 on specific commands but not others:**
- The OAuth2 client may lack permissions for write operations. Check the roles assigned to the client in Cribl.Cloud API Authentication settings.

**SSL Certificate errors:**
- Enable "Trust any certificate" in the instance configuration, or install the correct CA certificate in the XSOAR/XSIAM server's trust store.

**Empty results on pipeline, source, or destination commands:**
- These resources are managed at the Worker Group level. Pass the appropriate `worker_group` argument (e.g., `worker_group="default"`) to scope the request correctly. Without it, the command queries the Leader context, which may not have per-group resource data.

**Rate limiting (429):**
- The Cribl API applies rate limiting. Reduce playbook polling frequency or add a `Wait` task between repeated calls.
