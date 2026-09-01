# Cribl Search

## Overview

This integration connects Cortex XSOAR / XSIAM to the **Cribl Search** control-plane API (v2). It lets analysts and playbooks run ad-hoc searches over Cribl Lake, object stores (S3, GCS, Azure Blob), Cribl Edge/Leader, and federated third-party APIs, then retrieve the results as structured events. It also manages the objects that Cribl Search depends on: saved searches, datasets, dataset providers, dataset provider types, macros, and datatypes.

The typical automation flow is **create a search job → poll its status → fetch results**. See [Searching Cribl Lake](#searching-cribl-lake) for a worked example.

## Prerequisites

Cribl Search is only available on the **v2** REST API and is Cribl.Cloud–oriented. Authentication uses OAuth2 client credentials.

1. Log in to your Cribl.Cloud organization.
2. Go to **Settings > Global Settings > API Authentication** and create an API credential. Note the **Client ID** and **Client Secret**.
3. Assign the credential the roles it needs:
   * Running searches and reading results requires access to the Search product and to the datasets being queried.
   * Creating/updating/deleting datasets, dataset providers, macros, datatypes, and saved searches requires an admin or editor role for Search.
4. Determine your Search API base URL. It has the form:
   `https://main-<org>.cribl.cloud/api/v2/m/default_search`
   (`main-<org>.cribl.cloud` is your workspace host; `/api/v2/m/default_search` is the API version plus the Search product context.)

## Configuration

| Parameter | Description | Required |
|-----------|-------------|----------|
| Server URL | Base URL for the Cribl Search API, including the API version and search context path, e.g. `https://main-<org>.cribl.cloud/api/v2/m/default_search`. | Yes |
| Client ID | OAuth2 client ID from Cribl.Cloud **API Authentication** settings. | Yes |
| Client Secret | OAuth2 client secret. | Yes |
| Token URL | OAuth2 token endpoint. Defaults to `https://login.cribl.cloud/oauth/token`. Override only for on-premises deployments with a custom identity provider. | No |
| Trust any certificate (not secure) | Disable SSL certificate verification. Lab use only. | No |
| Use system proxy settings | Route API requests through the system proxy. | No |

The integration fetches an OAuth2 access token on first use and caches it (with its expiry) in the integration context, refreshing automatically when it is close to expiring.

## Searching Cribl Lake

Cribl Lake datasets are exposed to Cribl Search automatically. To search Lake data you run a normal search job whose query targets the Lake dataset — there is no separate "lake search" endpoint.

1. **Discover the dataset name** (optional):
   `!Cribl-search-list-datasets`
   Look for the Cribl Lake dataset ID you want (for example `cribl_lake_default_logs`).

2. **Start the search:**
   `!Cribl-search-create-job query="dataset=\"cribl_lake_default_logs\" | limit 1000" earliest="-1h" latest="now"`
   The command returns `CriblSearch.Job.id`.

3. **Poll until finished:**
   `!Cribl-search-get-job-status id="${CriblSearch.Job.id}"`
   Repeat (a `GenericPolling` / `Wait` loop in a playbook) until `CriblSearch.JobStatus.status` is `completed`.

4. **Fetch the results:**
   `!Cribl-search-get-job-results id="${CriblSearch.Job.id}" limit="1000"`
   The event objects land in `CriblSearch.SearchResult.events`; `CriblSearch.SearchResult.totalEventCount` is the full match count.

`Cribl-search-get-job-results-poll` behaves like step 4 but blocks server-side and returns as soon as the job status changes from the `last_job_status` you pass, which can reduce the number of poll iterations.

## Commands

### Search jobs

#### Cribl-search-list-jobs
**Description:** List search jobs, with optional filtering and pagination.

| Argument | Description | Required |
|----------|-------------|----------|
| output | Response format. Use `short` for abbreviated job info. | No |
| ids | Comma-separated job IDs to filter by. | No |
| type | Filter by job type (`standard`, `datatypePreview`, `scheduled`, `dashboard`, `command`, `notebook`, `systemInsights`, `agentic`, `metrics`). | No |
| earliest | Filter jobs by earliest time (relative string or epoch seconds). | No |
| latest | Filter jobs by latest time. Used when `output=short`. | No |
| filter_exp | Filter expression evaluated against jobs. | No |
| sort_exp | Sorting expression. | No |
| sort_dir | `asc` or `desc`. | No |
| limit | Maximum number of jobs to return. | No |
| offset | Starting offset for pagination. | No |

**Context Output:**

| Path | Type | Description |
|------|------|-------------|
| CriblSearch.Job.id | String | Unique identifier of the search job. |
| CriblSearch.Job.status | String | Lifecycle status of the job. |
| CriblSearch.Job.query | String | Query text submitted for the job. |
| CriblSearch.Job.user | String | Principal that created the job. |
| CriblSearch.Job.timeCreated | Number | Creation time (Unix ms). |
| CriblSearch.Job.timeCompleted | Number | Terminal-state time (Unix ms). |

**Example:** `!Cribl-search-list-jobs type=standard limit=20 sort_dir=desc`

---

#### Cribl-search-get-job
**Description:** Get a single search job by ID.

| Argument | Description | Required |
|----------|-------------|----------|
| id | The ID of the search job. | Yes |

**Context Output:**

| Path | Type | Description |
|------|------|-------------|
| CriblSearch.Job.id | String | Unique identifier of the search job. |
| CriblSearch.Job.status | String | Lifecycle status of the job. |
| CriblSearch.Job.query | String | Query text submitted for the job. |
| CriblSearch.Job.earliest | String | Lower bound of the search time window. |
| CriblSearch.Job.latest | String | Upper bound of the search time window. |
| CriblSearch.Job.timeCreated | Number | Creation time (Unix ms). |
| CriblSearch.Job.timeCompleted | Number | Terminal-state time (Unix ms). |
| CriblSearch.Job.totalEventCount | Number | Total result events for a completed job. |

**Example:** `!Cribl-search-get-job id="1700000000.1"`

---

#### Cribl-search-create-job
**Description:** Create (run) a search job. To search Cribl Lake, reference a Lake dataset in the query.

| Argument | Description | Required |
|----------|-------------|----------|
| query | The query to execute. | Yes |
| earliest | Earliest time in the range (relative string such as `-15m`, or epoch seconds). | No |
| latest | Latest time in the range (`now` or epoch seconds). | No |
| sample_rate | Sampling rate between 0 and 1. | No |
| timezone | IANA timezone identifier. | No |
| is_private | Whether results are accessible only to the owner. | No |
| num_events_before | Events to retrieve before the target event (contextual mode). | No |
| num_events_after | Events to retrieve after the target event (contextual mode). | No |
| target_event_time | Anchor event time (Unix ms) for contextual retrieval. | No |
| set_options | JSON object of `SET` option names to values. | No |
| expected_output_type | Output type expected from a System Insights query. | No |

**Context Output:**

| Path | Type | Description |
|------|------|-------------|
| CriblSearch.Job.id | String | Unique identifier of the created search job. |
| CriblSearch.Job.status | String | Lifecycle status of the job. |
| CriblSearch.Job.query | String | Query text submitted for the job. |
| CriblSearch.Job.earliest | String | Lower bound of the search time window. |
| CriblSearch.Job.latest | String | Upper bound of the search time window. |
| CriblSearch.Job.timeCreated | Number | Creation time (Unix ms). |

**Example:** `!Cribl-search-create-job query="dataset=\"cribl_lake_default_logs\" | limit 1000" earliest="-1h" latest="now"`

---

#### Cribl-search-update-job
**Description:** Update a search job. Supports transitioning the job to `completed` or `canceled` and toggling result privacy.

| Argument | Description | Required |
|----------|-------------|----------|
| id | The ID of the search job to update. | Yes |
| status | `completed` or `canceled`. | No |
| is_private | Whether results are accessible only to the owner. | No |

**Context Output:**

| Path | Type | Description |
|------|------|-------------|
| CriblSearch.Job.id | String | Unique identifier of the search job. |
| CriblSearch.Job.status | String | Lifecycle status of the job. |
| CriblSearch.Job.isPrivate | Boolean | Whether results are restricted to the owner. |

**Example:** `!Cribl-search-update-job id="1700000000.1" status=canceled`

---

#### Cribl-search-delete-job
**Description:** Delete a search job.

| Argument | Description | Required |
|----------|-------------|----------|
| id | The ID of the search job to delete. | Yes |

**Context Output:** None.

**Example:** `!Cribl-search-delete-job id="1700000000.1"`

---

#### Cribl-search-cancel-job
**Description:** Cancel a running search job.

| Argument | Description | Required |
|----------|-------------|----------|
| id | The ID of the search job to cancel. | Yes |

**Context Output:**

| Path | Type | Description |
|------|------|-------------|
| CriblSearch.Job.id | String | Unique identifier of the search job. |
| CriblSearch.Job.status | String | Lifecycle status after the cancel request. |
| CriblSearch.Job.timeCompleted | Number | Terminal-state time (Unix ms). |

**Example:** `!Cribl-search-cancel-job id="1700000000.1"`

---

#### Cribl-search-get-job-status
**Description:** Get execution status and progress counters for a search job.

| Argument | Description | Required |
|----------|-------------|----------|
| id | The ID of the search job. | Yes |
| advanced | If `true`, include stage-level details and ingestion metrics. | No |

**Context Output:**

| Path | Type | Description |
|------|------|-------------|
| CriblSearch.JobStatus.jobId | String | Unique identifier of the search job. |
| CriblSearch.JobStatus.status | String | Current lifecycle status. |
| CriblSearch.JobStatus.eventsFound | Number | Number of events that matched the query. |
| CriblSearch.JobStatus.objectsSearched | Number | Objects fully searched so far. |
| CriblSearch.JobStatus.objectsFound | Number | Objects discovered for the search to read. |
| CriblSearch.JobStatus.bytesIn | Number | Bytes scanned while executing the query. |
| CriblSearch.JobStatus.timeStarted | Number | Execution start time (Unix ms). |
| CriblSearch.JobStatus.timeCompleted | Number | Finish/cancel time (Unix ms). |

**Example:** `!Cribl-search-get-job-status id="1700000000.1" advanced=true`

---

#### Cribl-search-get-job-results
**Description:** Retrieve a page of search job results. Events are returned under `CriblSearch.SearchResult.events`.

| Argument | Description | Required |
|----------|-------------|----------|
| id | The ID of the search job to get results for. | Yes |
| limit | Maximum number of events to return. | No |
| offset | Starting offset of the events. | No |
| lower_bound | Lower bound of the time range, inclusive (epoch seconds). | No |
| upper_bound | Upper bound of the time range, exclusive (epoch seconds). | No |

**Context Output:**

| Path | Type | Description |
|------|------|-------------|
| CriblSearch.SearchResult.jobId | String | Unique identifier of the search job. |
| CriblSearch.SearchResult.isFinished | Boolean | Whether all result pages have been produced. |
| CriblSearch.SearchResult.totalEventCount | Number | Total number of events that matched the query. |
| CriblSearch.SearchResult.persistedEventCount | Number | Events persisted for the search job. |
| CriblSearch.SearchResult.offset | Number | Offset from the request that produced the page. |
| CriblSearch.SearchResult.limit | Number | Limit from the request that produced the page. |
| CriblSearch.SearchResult.events | Unknown | The result event objects for this page. |

**Example:** `!Cribl-search-get-job-results id="1700000000.1" limit=500`

---

#### Cribl-search-get-job-results-poll
**Description:** Retrieve results, returning immediately when the job status changes from `last_job_status`.

| Argument | Description | Required |
|----------|-------------|----------|
| id | The ID of the search job to poll results for. | Yes |
| limit | Maximum number of events to return. | No |
| offset | Starting offset of the events. | No |
| lower_bound | Lower bound of the time range, inclusive (epoch seconds). | No |
| upper_bound | Upper bound of the time range, exclusive (epoch seconds). | No |
| last_job_status | Last known job status; the call returns as soon as the status differs. | No |

**Context Output:** Same as `Cribl-search-get-job-results`.

**Example:** `!Cribl-search-get-job-results-poll id="1700000000.1" last_job_status=running limit=500`

---

#### Cribl-search-get-job-metrics
**Description:** Get the full metrics object for a search job.

| Argument | Description | Required |
|----------|-------------|----------|
| id | The ID of the search job to get metrics for. | Yes |

**Context Output:**

| Path | Type | Description |
|------|------|-------------|
| CriblSearch.JobMetrics.jobId | String | Unique identifier of the search job. |
| CriblSearch.JobMetrics.metrics | Unknown | The full metrics object. |

**Example:** `!Cribl-search-get-job-metrics id="1700000000.1"`

---

#### Cribl-search-get-job-timeline
**Description:** Get the per-bucket event count timeline for a search job.

| Argument | Description | Required |
|----------|-------------|----------|
| id | The ID of the search job to get the timeline for. | Yes |

**Context Output:**

| Path | Type | Description |
|------|------|-------------|
| CriblSearch.JobTimeline.jobId | String | Unique identifier of the search job. |
| CriblSearch.JobTimeline.totalEventCount | Number | Total events across all buckets. |
| CriblSearch.JobTimeline.buckets | Unknown | Event counts per time bucket. |

**Example:** `!Cribl-search-get-job-timeline id="1700000000.1"`

---

#### Cribl-search-get-job-field-summaries
**Description:** Get field statistics and top values for each field in a search job.

| Argument | Description | Required |
|----------|-------------|----------|
| id | The ID of the search job. | Yes |
| limit | Maximum number of fields to return. | No |
| offset | Pagination offset. | No |

**Context Output:**

| Path | Type | Description |
|------|------|-------------|
| CriblSearch.JobFieldSummary.jobId | String | Unique identifier of the search job. |
| CriblSearch.JobFieldSummary.totalEventCount | Number | Events considered for the summary. |
| CriblSearch.JobFieldSummary.partial | Boolean | Whether fields were omitted due to limits. |
| CriblSearch.JobFieldSummary.fields | Unknown | Field statistics and top values. |

**Example:** `!Cribl-search-get-job-field-summaries id="1700000000.1"`

---

#### Cribl-search-list-job-logs
**Description:** List the log filenames available for a search job.

| Argument | Description | Required |
|----------|-------------|----------|
| id | The ID of the search job. | Yes |
| limit | Maximum number of items to return. | No |
| offset | Pagination offset. | No |

**Context Output:**

| Path | Type | Description |
|------|------|-------------|
| CriblSearch.JobLog.jobId | String | Unique identifier of the search job. |
| CriblSearch.JobLog.logFiles | Unknown | Available log filenames. |

**Example:** `!Cribl-search-list-job-logs id="1700000000.1"`

---

#### Cribl-search-get-job-settings
**Description:** Get retention settings for a search job.

| Argument | Description | Required |
|----------|-------------|----------|
| id | The ID of the search job. | Yes |

**Context Output:**

| Path | Type | Description |
|------|------|-------------|
| CriblSearch.JobSettings.jobId | String | Unique identifier of the search job. |
| CriblSearch.JobSettings.reaperKeepUntil | Number | Retain-until timestamp (Unix ms). |

**Example:** `!Cribl-search-get-job-settings id="1700000000.1"`

---

#### Cribl-search-update-job-settings
**Description:** Update retention settings for a search job.

| Argument | Description | Required |
|----------|-------------|----------|
| id | The ID of the search job. | Yes |
| reaper_keep_until | Retain-until timestamp (Unix ms). | No |

**Context Output:**

| Path | Type | Description |
|------|------|-------------|
| CriblSearch.JobSettings.jobId | String | Unique identifier of the search job. |
| CriblSearch.JobSettings.reaperKeepUntil | Number | Retain-until timestamp (Unix ms). |

**Example:** `!Cribl-search-update-job-settings id="1700000000.1" reaper_keep_until=1735689600000`

---

### Saved searches

#### Cribl-search-list-saved-searches
**Description:** List saved searches, with optional pagination.

| Argument | Description | Required |
|----------|-------------|----------|
| limit | Maximum number of saved searches to return. | No |
| offset | Starting offset for pagination. | No |
| output | `short` for a compact list-view response. | No |
| resolve_datasets | If `true`, include resolved dataset identifiers. | No |
| dataset_ids | Return only saved searches associated with any of these dataset IDs (max 10). | No |

**Context Output:**

| Path | Type | Description |
|------|------|-------------|
| CriblSearch.SavedSearch.id | String | Unique identifier of the saved search. |
| CriblSearch.SavedSearch.name | String | Display name. |
| CriblSearch.SavedSearch.description | String | Description. |
| CriblSearch.SavedSearch.query | String | Query text. |
| CriblSearch.SavedSearch.user | String | Creator user identifier. |
| CriblSearch.SavedSearch.isPrivate | Boolean | Whether results are restricted to the owner. |

**Example:** `!Cribl-search-list-saved-searches limit=50`

---

#### Cribl-search-get-saved-search
**Description:** Get a single saved search by ID.

| Argument | Description | Required |
|----------|-------------|----------|
| id | The ID of the saved search. | Yes |

**Context Output:**

| Path | Type | Description |
|------|------|-------------|
| CriblSearch.SavedSearch.id | String | Unique identifier of the saved search. |
| CriblSearch.SavedSearch.name | String | Display name. |
| CriblSearch.SavedSearch.query | String | Query text. |
| CriblSearch.SavedSearch.earliest | String | Start of the search time range. |
| CriblSearch.SavedSearch.latest | String | End of the search time range. |

**Example:** `!Cribl-search-get-saved-search id="my-saved-search"`

---

#### Cribl-search-create-saved-search
**Description:** Create a saved search.

| Argument | Description | Required |
|----------|-------------|----------|
| id | Unique identifier for the saved search. | Yes |
| name | Display name. | Yes |
| query | Query text. | Yes |
| description | Brief description. | No |
| earliest | Start of the search time range. | No |
| latest | End of the search time range. | No |
| sample_rate | Sampling rate between 0 and 1. | No |
| timezone | IANA timezone for scheduled execution. | No |
| is_private | If `true`, results are restricted to the owner. | No |
| schedule | JSON object with the cron schedule and notification settings. | No |
| body | JSON object with additional fields; merged with explicit arguments (explicit arguments win). | No |

**Context Output:**

| Path | Type | Description |
|------|------|-------------|
| CriblSearch.SavedSearch.id | String | Unique identifier of the saved search. |
| CriblSearch.SavedSearch.name | String | Display name. |
| CriblSearch.SavedSearch.query | String | Query text. |

**Example:** `!Cribl-search-create-saved-search id="failed-logins" name="Failed Logins" query="dataset=\"cribl_lake_auth\" | where status==\"failed\""`

---

#### Cribl-search-update-saved-search
**Description:** Update a saved search.

| Argument | Description | Required |
|----------|-------------|----------|
| id | The ID of the saved search to update. | Yes |
| name | Display name. | No |
| query | Query text. | No |
| description | Brief description. | No |
| earliest | Start of the search time range. | No |
| latest | End of the search time range. | No |
| sample_rate | Sampling rate between 0 and 1. | No |
| timezone | IANA timezone for scheduled execution. | No |
| is_private | If `true`, results are restricted to the owner. | No |
| schedule | JSON object with the cron schedule and notification settings. | No |
| body | JSON object with additional fields; merged with explicit arguments (explicit arguments win). | No |

**Context Output:**

| Path | Type | Description |
|------|------|-------------|
| CriblSearch.SavedSearch.id | String | Unique identifier of the saved search. |
| CriblSearch.SavedSearch.name | String | Display name. |
| CriblSearch.SavedSearch.query | String | Query text. |

**Example:** `!Cribl-search-update-saved-search id="failed-logins" description="Auth failures in the last hour"`

---

#### Cribl-search-delete-saved-search
**Description:** Delete a saved search.

| Argument | Description | Required |
|----------|-------------|----------|
| id | The ID of the saved search to delete. | Yes |

**Context Output:** None.

**Example:** `!Cribl-search-delete-saved-search id="failed-logins"`

---

### Datasets

#### Cribl-search-list-datasets
**Description:** List datasets available to Cribl Search, including Cribl Lake datasets and federated data sources.

| Argument | Description | Required |
|----------|-------------|----------|
| limit | Maximum number of datasets to return. | No |
| offset | Starting offset for pagination. | No |
| explorer_stats | If `true`, include 30-day search counts. | No |
| last_used | If `true`, include the last-used timestamp. | No |
| favorites | If `true`, include favorite records. | No |
| vtables | If `true`, include virtual table definitions. | No |

**Context Output:**

| Path | Type | Description |
|------|------|-------------|
| CriblSearch.Dataset.id | String | Unique identifier of the dataset. |
| CriblSearch.Dataset.type | String | Dataset type identifier. |
| CriblSearch.Dataset.description | String | Description of the dataset. |

**Example:** `!Cribl-search-list-datasets limit=100`

---

#### Cribl-search-get-dataset
**Description:** Get a single dataset by ID.

| Argument | Description | Required |
|----------|-------------|----------|
| id | The ID of the dataset. | Yes |

**Context Output:**

| Path | Type | Description |
|------|------|-------------|
| CriblSearch.Dataset.id | String | Unique identifier of the dataset. |
| CriblSearch.Dataset.type | String | Dataset type identifier. |
| CriblSearch.Dataset.description | String | Description of the dataset. |

**Example:** `!Cribl-search-get-dataset id="cribl_lake_default_logs"`

---

#### Cribl-search-create-dataset
**Description:** Create a dataset. Dataset bodies are polymorphic and depend on the dataset type; supply the full definition as JSON.

| Argument | Description | Required |
|----------|-------------|----------|
| body | JSON object with the full dataset definition (must include `type` and type-specific configuration). | Yes |

**Context Output:**

| Path | Type | Description |
|------|------|-------------|
| CriblSearch.Dataset.id | String | Unique identifier of the created dataset. |
| CriblSearch.Dataset.type | String | Dataset type identifier. |

**Example:** `!Cribl-search-create-dataset body="{\"id\":\"s3-archive\",\"type\":\"s3\",\"bucket\":\"my-log-archive\",\"region\":\"us-east-1\"}"`

---

#### Cribl-search-update-dataset
**Description:** Update a dataset. Supply the full updated definition as JSON.

| Argument | Description | Required |
|----------|-------------|----------|
| id | The ID of the dataset to update. | Yes |
| body | JSON object with the full updated dataset definition. | Yes |

**Context Output:**

| Path | Type | Description |
|------|------|-------------|
| CriblSearch.Dataset.id | String | Unique identifier of the dataset. |
| CriblSearch.Dataset.type | String | Dataset type identifier. |

**Example:** `!Cribl-search-update-dataset id="s3-archive" body="{\"id\":\"s3-archive\",\"type\":\"s3\",\"bucket\":\"my-log-archive\",\"region\":\"us-west-2\"}"`

---

#### Cribl-search-delete-dataset
**Description:** Delete a dataset.

| Argument | Description | Required |
|----------|-------------|----------|
| id | The ID of the dataset to delete. | Yes |

**Context Output:** None.

**Example:** `!Cribl-search-delete-dataset id="s3-archive"`

---

#### Cribl-search-delete-dataset-data
**Description:** Remove **all** ingested events from a Cribl Search dataset. This permanently deletes data.

| Argument | Description | Required |
|----------|-------------|----------|
| id | The ID of the Cribl Search dataset to clear. | Yes |

**Context Output:** None.

**Example:** `!Cribl-search-delete-dataset-data id="cribl_search_sample"`

---

#### Cribl-search-get-dataset-fields
**Description:** Get lakehouse-engine dataset field names over a time window. Defaults to the last 24 hours with 1-hour buckets.

| Argument | Description | Required |
|----------|-------------|----------|
| id | The ID of the dataset. | Yes |
| start_time | Window start (relative string, ISO 8601, or epoch). Defaults to 24h ago. | No |
| end_time | Window end. Defaults to now. | No |
| granularity | Bucket width in milliseconds. Defaults to 3600000. | No |
| top_values | If `true`, also return each field's most frequent values. | No |

**Context Output:**

| Path | Type | Description |
|------|------|-------------|
| CriblSearch.DatasetField.datasetId | String | Unique identifier of the dataset. |
| CriblSearch.DatasetField.fields | Unknown | Field names, ordered by descending event count. |
| CriblSearch.DatasetField.topValues | Unknown | Each field's most frequent values. |

**Example:** `!Cribl-search-get-dataset-fields id="cribl_lake_default_logs" start_time="-7d"`

---

#### Cribl-search-get-dataset-stats
**Description:** Get lakehouse-engine dataset statistics (event/byte counts, min/max event time) over a time window. Defaults to the last 24 hours with 1-hour buckets.

| Argument | Description | Required |
|----------|-------------|----------|
| id | The ID of the dataset. | Yes |
| start_time | Window start. Defaults to 24h ago. | No |
| end_time | Window end. Defaults to now. | No |
| granularity | Bucket width in milliseconds. Defaults to 3600000. | No |

**Context Output:**

| Path | Type | Description |
|------|------|-------------|
| CriblSearch.DatasetStats.datasetId | String | Unique identifier of the dataset. |
| CriblSearch.DatasetStats.totalEventCount | Number | Total events in the dataset. |
| CriblSearch.DatasetStats.totalByteCount | Number | Total bytes in the dataset. |
| CriblSearch.DatasetStats.minEventTime | Number | Earliest event timestamp (Unix ms). |
| CriblSearch.DatasetStats.maxEventTime | Number | Latest event timestamp (Unix ms). |
| CriblSearch.DatasetStats.eventCounts | Unknown | Time series of event counts. |

**Example:** `!Cribl-search-get-dataset-stats id="cribl_lake_default_logs"`

---

#### Cribl-search-get-dataset-field-stats
**Description:** Get lakehouse-engine per-field statistics for a dataset over a time window. Defaults to the last 24 hours with 1-hour buckets.

| Argument | Description | Required |
|----------|-------------|----------|
| id | The ID of the dataset. | Yes |
| start_time | Window start. Defaults to 24h ago. | No |
| end_time | Window end. Defaults to now. | No |
| granularity | Bucket width in milliseconds. Defaults to 3600000. | No |
| limit | Maximum number of fields to return (capped at 1000). | No |
| offset | Number of fields to skip. | No |
| sort | Dimension used to order fields (for example `highestPresence`, `lowestPresence`). | No |
| filter | Case-insensitive substring matched against field names. | No |

**Context Output:**

| Path | Type | Description |
|------|------|-------------|
| CriblSearch.DatasetFieldStats.datasetId | String | Unique identifier of the dataset. |
| CriblSearch.DatasetFieldStats.totalEventCount | Number | Total events over the time window. |
| CriblSearch.DatasetFieldStats.totalFieldCount | Number | Fields matching the filter across the dataset. |
| CriblSearch.DatasetFieldStats.fieldStats | Unknown | Array of per-field statistics. |

**Example:** `!Cribl-search-get-dataset-field-stats id="cribl_lake_default_logs" sort=highestPresence limit=50`

---

#### Cribl-search-get-dataset-dimension-stats
**Description:** Get dimension (label) statistics for a customer-metrics dataset over a time window. Defaults to the last 24 hours with 1-hour buckets.

| Argument | Description | Required |
|----------|-------------|----------|
| id | The ID of the customer-metrics dataset. | Yes |
| start_time | Window start. Defaults to 24h ago. | No |
| end_time | Window end. Defaults to now. | No |
| granularity | Bucket width in milliseconds. Defaults to 3600000. | No |
| metric_name | Metric name filter. All metrics are considered when omitted. | No |
| limit | Maximum number of dimensions to return. Defaults to 100. | No |
| top_values_limit | Maximum number of top values per dimension. Defaults to 10. | No |

**Context Output:**

| Path | Type | Description |
|------|------|-------------|
| CriblSearch.DatasetDimensionStats.datasetId | String | Unique identifier of the dataset. |
| CriblSearch.DatasetDimensionStats.totalSampleCount | Number | Metric samples considered. |
| CriblSearch.DatasetDimensionStats.totalSeriesCount | Number | Metric series considered. |
| CriblSearch.DatasetDimensionStats.dimensionStats | Unknown | Per-dimension statistics. |

**Example:** `!Cribl-search-get-dataset-dimension-stats id="cribl_metrics" metric_name="cpu.percent"`

---

#### Cribl-search-get-dataset-usage-stats
**Description:** Get lakehouse-engine query usage statistics for a dataset.

| Argument | Description | Required |
|----------|-------------|----------|
| id | The ID of the dataset. | Yes |
| end_time | Window end. Defaults to the current server time. | No |
| time_window | Window duration in milliseconds, counted back from `end_time`. | No |
| granularity | Bucket width in milliseconds (multiple of 1 minute, ≤ 24 hours). | No |

**Context Output:**

| Path | Type | Description |
|------|------|-------------|
| CriblSearch.DatasetUsageStats.datasetId | String | Unique identifier of the dataset. |
| CriblSearch.DatasetUsageStats.lastQueryTime | Number | Most recent query timestamp (Unix ms). |
| CriblSearch.DatasetUsageStats.queryCounts | Unknown | Sparse histogram of query counts. |
| CriblSearch.DatasetUsageStats.topUsers | Unknown | Users with the most queries. |

**Example:** `!Cribl-search-get-dataset-usage-stats id="cribl_lake_default_logs"`

---

### Dataset providers

#### Cribl-search-list-dataset-providers
**Description:** List dataset providers (Cribl.Cloud only).

| Argument | Description | Required |
|----------|-------------|----------|
| limit | Maximum number of dataset providers to return. | No |
| offset | Starting offset for pagination. | No |

**Context Output:**

| Path | Type | Description |
|------|------|-------------|
| CriblSearch.DatasetProvider.id | String | Unique identifier of the dataset provider. |
| CriblSearch.DatasetProvider.type | String | Dataset provider type identifier. |
| CriblSearch.DatasetProvider.description | String | Description. |

**Example:** `!Cribl-search-list-dataset-providers`

---

#### Cribl-search-get-dataset-provider
**Description:** Get a single dataset provider by ID (Cribl.Cloud only).

| Argument | Description | Required |
|----------|-------------|----------|
| id | The ID of the dataset provider. | Yes |

**Context Output:**

| Path | Type | Description |
|------|------|-------------|
| CriblSearch.DatasetProvider.id | String | Unique identifier of the dataset provider. |
| CriblSearch.DatasetProvider.type | String | Dataset provider type identifier. |
| CriblSearch.DatasetProvider.description | String | Description. |

**Example:** `!Cribl-search-get-dataset-provider id="aws-prod"`

---

#### Cribl-search-create-dataset-provider
**Description:** Create a dataset provider (Cribl.Cloud only). Provider bodies are polymorphic; supply the full definition as JSON.

| Argument | Description | Required |
|----------|-------------|----------|
| body | JSON object with the full dataset provider definition (must include `type` and type-specific configuration). | Yes |

**Context Output:**

| Path | Type | Description |
|------|------|-------------|
| CriblSearch.DatasetProvider.id | String | Unique identifier of the created dataset provider. |
| CriblSearch.DatasetProvider.type | String | Dataset provider type identifier. |

**Example:** `!Cribl-search-create-dataset-provider body="{\"id\":\"aws-prod\",\"type\":\"api_aws\",\"accountConfigs\":[{\"name\":\"default\",\"awsApiKey\":\"...\",\"awsSecretKey\":\"...\"}]}"`

---

#### Cribl-search-update-dataset-provider
**Description:** Update a dataset provider (Cribl.Cloud only). Supply the full updated definition as JSON.

| Argument | Description | Required |
|----------|-------------|----------|
| id | The ID of the dataset provider to update. | Yes |
| body | JSON object with the full updated dataset provider definition. | Yes |

**Context Output:**

| Path | Type | Description |
|------|------|-------------|
| CriblSearch.DatasetProvider.id | String | Unique identifier of the dataset provider. |
| CriblSearch.DatasetProvider.type | String | Dataset provider type identifier. |

**Example:** `!Cribl-search-update-dataset-provider id="aws-prod" body="{\"id\":\"aws-prod\",\"type\":\"api_aws\",\"description\":\"Prod AWS\"}"`

---

#### Cribl-search-delete-dataset-provider
**Description:** Delete a dataset provider (Cribl.Cloud only).

| Argument | Description | Required |
|----------|-------------|----------|
| id | The ID of the dataset provider to delete. | Yes |

**Context Output:** None.

**Example:** `!Cribl-search-delete-dataset-provider id="aws-prod"`

---

#### Cribl-search-get-dataset-provider-details
**Description:** Get discovery data for a dataset provider (Cribl.Cloud only).

| Argument | Description | Required |
|----------|-------------|----------|
| id | The ID of the dataset provider. | Yes |

**Context Output:**

| Path | Type | Description |
|------|------|-------------|
| CriblSearch.DatasetProviderDetails.id | String | Unique identifier of the dataset provider. |
| CriblSearch.DatasetProviderDetails.bucketNames | Unknown | Discovered bucket names, when applicable. |

**Example:** `!Cribl-search-get-dataset-provider-details id="asl-prod"`

---

#### Cribl-search-list-dataset-provider-types
**Description:** List dataset provider types and their supported capabilities (Cribl.Cloud only).

| Argument | Description | Required |
|----------|-------------|----------|
| limit | Maximum number of items to return. | No |
| offset | Pagination offset. | No |

**Context Output:**

| Path | Type | Description |
|------|------|-------------|
| CriblSearch.DatasetProviderType.id | String | Type identifier (for example `cribl_lake`, `s3`, `api_http`). |
| CriblSearch.DatasetProviderType.description | String | Description of the type. |
| CriblSearch.DatasetProviderType.capabilities | Unknown | Supported operations for the type. |

**Example:** `!Cribl-search-list-dataset-provider-types`

---

#### Cribl-search-get-dataset-provider-type
**Description:** Get a single dataset provider type by ID (Cribl.Cloud only).

| Argument | Description | Required |
|----------|-------------|----------|
| id | The dataset provider type identifier. | Yes |

**Context Output:**

| Path | Type | Description |
|------|------|-------------|
| CriblSearch.DatasetProviderType.id | String | Type identifier. |
| CriblSearch.DatasetProviderType.description | String | Description of the type. |
| CriblSearch.DatasetProviderType.capabilities | Unknown | Supported operations for the type. |

**Example:** `!Cribl-search-get-dataset-provider-type id="cribl_lake"`

---

### Macros

#### Cribl-search-list-macros
**Description:** List search macros.

| Argument | Description | Required |
|----------|-------------|----------|
| limit | Maximum number of macros to return. | No |
| offset | Starting offset for pagination. | No |

**Context Output:**

| Path | Type | Description |
|------|------|-------------|
| CriblSearch.Macro.id | String | Unique identifier of the macro. |
| CriblSearch.Macro.replacement | String | Query fragment substituted when referenced. |
| CriblSearch.Macro.description | String | Description. |
| CriblSearch.Macro.tags | String | Tag used to filter macros. |

**Example:** `!Cribl-search-list-macros`

---

#### Cribl-search-get-macro
**Description:** Get a single search macro by ID.

| Argument | Description | Required |
|----------|-------------|----------|
| id | The ID of the macro. | Yes |

**Context Output:**

| Path | Type | Description |
|------|------|-------------|
| CriblSearch.Macro.id | String | Unique identifier of the macro. |
| CriblSearch.Macro.replacement | String | Query fragment substituted when referenced. |
| CriblSearch.Macro.description | String | Description. |

**Example:** `!Cribl-search-get-macro id="last24h"`

---

#### Cribl-search-create-macro
**Description:** Create a search macro.

| Argument | Description | Required |
|----------|-------------|----------|
| id | Unique identifier for the macro. | Yes |
| replacement | Query fragment substituted when the macro is referenced. | Yes |
| description | Brief description. | No |
| tags | Tag used to filter macros. | No |

**Context Output:**

| Path | Type | Description |
|------|------|-------------|
| CriblSearch.Macro.id | String | Unique identifier of the macro. |
| CriblSearch.Macro.replacement | String | Query fragment substituted when referenced. |

**Example:** `!Cribl-search-create-macro id="err_only" replacement="| where level=='error'" description="Filter to error events"`

---

#### Cribl-search-update-macro
**Description:** Update a search macro.

| Argument | Description | Required |
|----------|-------------|----------|
| id | The ID of the macro to update. | Yes |
| replacement | Query fragment substituted when the macro is referenced. | No |
| description | Brief description. | No |
| tags | Tag used to filter macros. | No |

**Context Output:**

| Path | Type | Description |
|------|------|-------------|
| CriblSearch.Macro.id | String | Unique identifier of the macro. |
| CriblSearch.Macro.replacement | String | Query fragment substituted when referenced. |

**Example:** `!Cribl-search-update-macro id="err_only" description="Filter to error and fatal events"`

---

#### Cribl-search-delete-macro
**Description:** Delete a search macro.

| Argument | Description | Required |
|----------|-------------|----------|
| id | The ID of the macro to delete. | Yes |

**Context Output:** None.

**Example:** `!Cribl-search-delete-macro id="err_only"`

---

### Datatypes

#### Cribl-search-list-datatypes
**Description:** List datatypes.

| Argument | Description | Required |
|----------|-------------|----------|
| limit | Maximum number of datatypes to return. | No |
| offset | Starting offset for pagination. | No |

**Context Output:**

| Path | Type | Description |
|------|------|-------------|
| CriblSearch.Datatype.id | String | Unique identifier of the datatype. |
| CriblSearch.Datatype.dataFormat | String | Data format (`ndjson`, `delimited`, `json_array`, `kvp`, `parquet`, `raw`, `splunk_journal`, `xml`). |
| CriblSearch.Datatype.lib | String | Library scope (`cribl`, `cribl-custom`, `custom`). |
| CriblSearch.Datatype.description | String | Description. |
| CriblSearch.Datatype.tags | String | Comma-separated tags. |

**Example:** `!Cribl-search-list-datatypes`

---

#### Cribl-search-get-datatype
**Description:** Get a single datatype by ID.

| Argument | Description | Required |
|----------|-------------|----------|
| id | The ID of the datatype. | Yes |

**Context Output:**

| Path | Type | Description |
|------|------|-------------|
| CriblSearch.Datatype.id | String | Unique identifier of the datatype. |
| CriblSearch.Datatype.dataFormat | String | Data format. |
| CriblSearch.Datatype.description | String | Description. |

**Example:** `!Cribl-search-get-datatype id="my-json-logs"`

---

#### Cribl-search-create-datatype
**Description:** Create a datatype. Datatype bodies are polymorphic and depend on the data format; supply the full definition as JSON.

| Argument | Description | Required |
|----------|-------------|----------|
| body | JSON object with the full datatype definition (must include `id`, `dataFormat`, `lib`, and `timestampExtraction`). | Yes |

**Context Output:**

| Path | Type | Description |
|------|------|-------------|
| CriblSearch.Datatype.id | String | Unique identifier of the created datatype. |
| CriblSearch.Datatype.dataFormat | String | Data format. |

**Example:** `!Cribl-search-create-datatype body="{\"id\":\"my-json-logs\",\"lib\":\"custom\",\"dataFormat\":\"ndjson\",\"automaticExtraction\":{\"extractionType\":\"json\"},\"timestampExtraction\":{\"type\":\"auto\"}}"`

---

#### Cribl-search-update-datatype
**Description:** Update a datatype. Supply the full updated definition as JSON.

| Argument | Description | Required |
|----------|-------------|----------|
| id | The ID of the datatype to update. | Yes |
| body | JSON object with the full updated datatype definition. | Yes |

**Context Output:**

| Path | Type | Description |
|------|------|-------------|
| CriblSearch.Datatype.id | String | Unique identifier of the datatype. |
| CriblSearch.Datatype.dataFormat | String | Data format. |

**Example:** `!Cribl-search-update-datatype id="my-json-logs" body="{\"id\":\"my-json-logs\",\"lib\":\"custom\",\"dataFormat\":\"ndjson\",\"description\":\"App JSON logs\",\"automaticExtraction\":{\"extractionType\":\"json\"},\"timestampExtraction\":{\"type\":\"auto\"}}"`

---

#### Cribl-search-delete-datatype
**Description:** Delete a datatype.

| Argument | Description | Required |
|----------|-------------|----------|
| id | The ID of the datatype to delete. | Yes |

**Context Output:**

| Path | Type | Description |
|------|------|-------------|
| CriblSearch.Datatype.id | String | Unique identifier of the deleted datatype. |

**Example:** `!Cribl-search-delete-datatype id="my-json-logs"`

---

## Troubleshooting

**Authorization Error on Test:**
- Confirm the Client ID and Client Secret are correct and created under **Settings > Global Settings > API Authentication** in Cribl.Cloud.
- Confirm the credential has access to the Search product.
- For on-prem with a custom identity provider, set the **Token URL** to that provider's token endpoint.

**404 on Test or on every command:**
- The Server URL must include the API version and Search context, for example `https://main-<org>.cribl.cloud/api/v2/m/default_search`. Cribl Search is not available on `/api/v1`.

**401 on write commands but not reads:**
- The OAuth2 credential likely lacks an editor/admin role for Search. Adjust its roles in Cribl.Cloud.

**`get-job-results` returns no events but the job completed:**
- Increase `limit`, or check `CriblSearch.SearchResult.totalEventCount`. If it is `0`, the query matched nothing in the given time range.
- Results for a job are only retained for a limited time; fetch them shortly after completion or raise the retention window with `Cribl-search-update-job-settings`.

**Dataset stats / fields commands return an error:**
- These endpoints are backed by the Cribl lakehouse engine and only work for datasets that have lakehouse acceleration or are customer-metrics datasets.

**Rate limiting / concurrency (429):**
- Cribl Search enforces search concurrency and usage guardrails. Reduce parallel `Cribl-search-create-job` calls or add a `Wait` between them in playbooks.
