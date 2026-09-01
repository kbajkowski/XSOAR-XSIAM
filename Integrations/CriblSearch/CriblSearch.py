import json
import time


VENDOR_NAME = 'CriblSearch'
CRIBL_CLOUD_TOKEN_URL = 'https://login.cribl.cloud/oauth/token'
CRIBL_CLOUD_AUDIENCE = 'https://api.cribl.cloud'

# Default look-back window (24h) and bucket size (1h) for the lakehouse-engine
# Dataset statistics endpoints, which require an explicit time range in ms.
DEFAULT_STATS_WINDOW_MS = 24 * 60 * 60 * 1000
DEFAULT_STATS_GRANULARITY_MS = 60 * 60 * 1000


""" HELPERS """


def is_token_expired(expiry_timestamp: int, buffer_seconds: int = 60) -> bool:
    return int(time.time()) >= (expiry_timestamp - buffer_seconds)


def create_expiry_timestamp(expires_in: int) -> int:
    return int(time.time()) + expires_in


def to_items(response) -> list:
    """Normalize a Cribl response to a list.

    List endpoints return ``{"items": [...], "count": N}`` while single-resource,
    create, update, and delete endpoints return the bare object.
    """
    if isinstance(response, list):
        return response
    if isinstance(response, dict):
        if 'items' in response and isinstance(response['items'], list):
            return response['items']
        return [response]
    return [response] if response is not None else []


def parse_json_arg(value: str | None, arg_name: str) -> dict:
    if not value:
        return {}
    try:
        parsed = json.loads(value)
    except ValueError as e:
        raise DemistoException(f'Invalid JSON in "{arg_name}" argument: {e}')
    if not isinstance(parsed, dict):
        raise DemistoException(f'The "{arg_name}" argument must be a JSON object.')
    return parsed


def resolve_stats_window(args: dict) -> tuple[int, int, int]:
    """Return (start_time_ms, end_time_ms, granularity_ms) for the stats endpoints."""
    end_dt = arg_to_datetime(args.get('end_time'))
    end_ms = int(end_dt.timestamp() * 1000) if end_dt else int(time.time() * 1000)
    start_dt = arg_to_datetime(args.get('start_time'))
    start_ms = int(start_dt.timestamp() * 1000) if start_dt else end_ms - DEFAULT_STATS_WINDOW_MS
    granularity_ms = arg_to_number(args.get('granularity')) or DEFAULT_STATS_GRANULARITY_MS
    return start_ms, end_ms, granularity_ms


""" CLIENT """


class Client(BaseClient):
    def __init__(self, base_url: str, api_key: str, verify: bool, proxy: bool):
        super().__init__(
            base_url=base_url,
            verify=verify,
            proxy=proxy,
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            },
        )

    def get_token(self, client_id: str, client_secret: str, token_url: str) -> dict:
        body = {
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret,
            'audience': CRIBL_CLOUD_AUDIENCE,
        }
        return self._http_request('POST', full_url=token_url, json_data=body)

    # --- Search Jobs ---

    def list_jobs(self, params: dict) -> dict:
        return self._http_request('GET', '/search/jobs', params=params)

    def get_job(self, job_id: str) -> dict:
        return self._http_request('GET', f'/search/jobs/{job_id}')

    def create_job(self, body: dict) -> dict:
        return self._http_request('POST', '/search/jobs', json_data=body)

    def update_job(self, job_id: str, body: dict) -> dict:
        return self._http_request('PATCH', f'/search/jobs/{job_id}', json_data=body)

    def delete_job(self, job_id: str) -> dict:
        return self._http_request('DELETE', f'/search/jobs/{job_id}', resp_type='response', ok_codes=(200, 204))

    def cancel_job(self, job_id: str) -> dict:
        return self._http_request('POST', f'/search/jobs/{job_id}/cancel', json_data={})

    def get_job_status(self, job_id: str, advanced: bool | None) -> dict:
        params = assign_params(advanced=advanced)
        return self._http_request('GET', f'/search/jobs/{job_id}/status', params=params)

    def get_job_results(self, job_id: str, params: dict) -> str:
        # Results are streamed as newline-delimited JSON (application/x-ndjson).
        return self._http_request('GET', f'/search/jobs/{job_id}/results', params=params, resp_type='text')

    def get_job_results_poll(self, job_id: str, params: dict) -> str:
        return self._http_request('GET', f'/search/jobs/{job_id}/results-poll', params=params, resp_type='text')

    def get_job_metrics(self, job_id: str) -> dict:
        return self._http_request('GET', f'/search/jobs/{job_id}/metrics')

    def get_job_timeline(self, job_id: str) -> dict:
        return self._http_request('GET', f'/search/jobs/{job_id}/timeline')

    def get_job_field_summaries(self, job_id: str, params: dict) -> dict:
        return self._http_request('GET', f'/search/jobs/{job_id}/field-summaries', params=params)

    def list_job_logs(self, job_id: str, params: dict) -> dict:
        return self._http_request('GET', f'/search/jobs/{job_id}/logs', params=params)

    def get_job_settings(self, job_id: str) -> dict:
        return self._http_request('GET', f'/search/jobs/{job_id}/settings')

    def update_job_settings(self, job_id: str, body: dict) -> dict:
        return self._http_request('POST', f'/search/jobs/{job_id}/settings', json_data=body)

    # --- Saved Searches ---

    def list_saved_searches(self, params: dict) -> dict:
        return self._http_request('GET', '/search/saved', params=params)

    def get_saved_search(self, saved_id: str) -> dict:
        return self._http_request('GET', f'/search/saved/{saved_id}')

    def create_saved_search(self, body: dict) -> dict:
        return self._http_request('POST', '/search/saved', json_data=body)

    def update_saved_search(self, saved_id: str, body: dict) -> dict:
        return self._http_request('PATCH', f'/search/saved/{saved_id}', json_data=body)

    def delete_saved_search(self, saved_id: str) -> dict:
        return self._http_request('DELETE', f'/search/saved/{saved_id}', resp_type='response', ok_codes=(200, 204))

    # --- Datasets ---

    def list_datasets(self, params: dict) -> dict:
        return self._http_request('GET', '/search/datasets', params=params)

    def get_dataset(self, dataset_id: str) -> dict:
        return self._http_request('GET', f'/search/datasets/{dataset_id}')

    def create_dataset(self, body: dict) -> dict:
        return self._http_request('POST', '/search/datasets', json_data=body)

    def update_dataset(self, dataset_id: str, body: dict) -> dict:
        return self._http_request('PATCH', f'/search/datasets/{dataset_id}', json_data=body)

    def delete_dataset(self, dataset_id: str) -> dict:
        return self._http_request('DELETE', f'/search/datasets/{dataset_id}', resp_type='response', ok_codes=(200, 204))

    def delete_dataset_data(self, dataset_id: str) -> dict:
        return self._http_request('DELETE', f'/search/datasets/{dataset_id}/data', resp_type='response', ok_codes=(200, 204))

    def get_dataset_fields(self, dataset_id: str, params: dict) -> dict:
        return self._http_request('GET', f'/search/datasets/{dataset_id}/fields', params=params)

    def get_dataset_stats(self, dataset_id: str, params: dict) -> dict:
        return self._http_request('GET', f'/search/datasets/{dataset_id}/datasetStats', params=params)

    def get_dataset_field_stats(self, dataset_id: str, params: dict) -> dict:
        return self._http_request('GET', f'/search/datasets/{dataset_id}/fieldStats', params=params)

    def get_dataset_dimension_stats(self, dataset_id: str, params: dict) -> dict:
        return self._http_request('GET', f'/search/datasets/{dataset_id}/dimensionStats', params=params)

    def get_dataset_usage_stats(self, dataset_id: str, params: dict) -> dict:
        return self._http_request('GET', f'/search/datasets/{dataset_id}/usageStats', params=params)

    # --- Dataset Providers ---

    def list_dataset_providers(self, params: dict) -> dict:
        return self._http_request('GET', '/search/dataset-providers', params=params)

    def get_dataset_provider(self, provider_id: str) -> dict:
        return self._http_request('GET', f'/search/dataset-providers/{provider_id}')

    def create_dataset_provider(self, body: dict) -> dict:
        return self._http_request('POST', '/search/dataset-providers', json_data=body)

    def update_dataset_provider(self, provider_id: str, body: dict) -> dict:
        return self._http_request('PATCH', f'/search/dataset-providers/{provider_id}', json_data=body)

    def delete_dataset_provider(self, provider_id: str) -> dict:
        return self._http_request('DELETE', f'/search/dataset-providers/{provider_id}',
                                  resp_type='response', ok_codes=(200, 204))

    def get_dataset_provider_details(self, provider_id: str) -> dict:
        return self._http_request('GET', f'/search/dataset-providers/{provider_id}/details')

    # --- Dataset Provider Types ---

    def list_dataset_provider_types(self, params: dict) -> dict:
        return self._http_request('GET', '/search/dataset-provider-types', params=params)

    def get_dataset_provider_type(self, type_id: str) -> dict:
        return self._http_request('GET', f'/search/dataset-provider-types/{type_id}')

    # --- Macros ---

    def list_macros(self, params: dict) -> dict:
        return self._http_request('GET', '/search/macros', params=params)

    def get_macro(self, macro_id: str) -> dict:
        return self._http_request('GET', f'/search/macros/{macro_id}')

    def create_macro(self, body: dict) -> dict:
        return self._http_request('POST', '/search/macros', json_data=body)

    def update_macro(self, macro_id: str, body: dict) -> dict:
        return self._http_request('PATCH', f'/search/macros/{macro_id}', json_data=body)

    def delete_macro(self, macro_id: str) -> dict:
        return self._http_request('DELETE', f'/search/macros/{macro_id}', resp_type='response', ok_codes=(200, 204))

    # --- Datatypes ---

    def list_datatypes(self, params: dict) -> dict:
        return self._http_request('GET', '/search/datatypes', params=params)

    def get_datatype(self, datatype_id: str) -> dict:
        return self._http_request('GET', f'/search/datatypes/{datatype_id}')

    def create_datatype(self, body: dict) -> dict:
        return self._http_request('POST', '/search/datatypes', json_data=body)

    def update_datatype(self, datatype_id: str, body: dict) -> dict:
        return self._http_request('PATCH', f'/search/datatypes/{datatype_id}', json_data=body)

    def delete_datatype(self, datatype_id: str) -> dict:
        return self._http_request('DELETE', f'/search/datatypes/{datatype_id}', resp_type='response', ok_codes=(200, 204))


""" TOKEN MANAGEMENT """


def get_valid_token(auth_client: 'Client', client_id: str, client_secret: str, token_url: str) -> str:
    """Return a cached token, refreshing via OAuth2 client credentials if expired or absent."""
    ctx = get_integration_context()
    token = ctx.get('token')
    expiry = ctx.get('expiry')

    if not token or not expiry or is_token_expired(expiry):
        demisto.debug('CriblSearch: token missing or expired, fetching new token')
        token_data = auth_client.get_token(client_id, client_secret, token_url)
        token = token_data.get('access_token')
        if not token:
            raise DemistoException('Failed to obtain access_token from Cribl Cloud. Check Client ID and Client Secret.')
        expiry = create_expiry_timestamp(token_data.get('expires_in', 3600))
        set_integration_context({'token': token, 'expiry': expiry})

    return token


""" RESULT PARSING """


def parse_ndjson(raw: str) -> tuple[dict, list]:
    """Split a Cribl NDJSON results stream into (summary, events).

    The stream is one JSON object per line. The header/summary line carries job
    metadata (``totalEventCount``, ``job``, ``isFinished``); every other line is
    a result event.
    """
    summary: dict = {}
    events: list = []
    for line in (raw or '').splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except ValueError:
            continue
        if isinstance(obj, dict) and not summary and ('totalEventCount' in obj or 'job' in obj or 'isFinished' in obj):
            summary = obj
        else:
            events.append(obj)
    return summary, events


""" TEST MODULE """


def test_module(auth_client: 'Client', client_id: str, client_secret: str, token_url: str,
                base_url: str, verify: bool, proxy: bool) -> str:
    try:
        token_data = auth_client.get_token(client_id, client_secret, token_url)
        if not token_data.get('access_token'):
            return 'Authorization Error: no access_token in response. Check Client ID and Client Secret.'
        client = Client(base_url=base_url, api_key=token_data['access_token'], verify=verify, proxy=proxy)
        client.list_jobs({'limit': 1})
        return 'ok'
    except DemistoException as e:
        if '401' in str(e) or 'Unauthorized' in str(e) or 'access_denied' in str(e):
            return 'Authorization Error: make sure Client ID and Client Secret are correct.'
        if '404' in str(e):
            return ('Not Found: verify the Server URL includes the API version and search context path, '
                    'e.g. https://main-<org>.cribl.cloud/api/v2/m/default_search')
        raise


""" COMMAND FUNCTIONS - SEARCH JOBS """


def list_jobs_command(client: Client, args: dict) -> CommandResults:
    params = assign_params(
        output=args.get('output'),
        id=argToList(args.get('ids')) or None,
        type=args.get('type'),
        earliest=args.get('earliest'),
        latest=args.get('latest'),
        filterExp=args.get('filter_exp'),
        sortExp=args.get('sort_exp'),
        sortDir=args.get('sort_dir'),
        limit=arg_to_number(args.get('limit')),
        offset=arg_to_number(args.get('offset')),
    )
    response = client.list_jobs(params)
    items = to_items(response)
    return CommandResults(
        outputs_prefix='CriblSearch.Job',
        outputs_key_field='id',
        outputs=items,
        readable_output=tableToMarkdown('Cribl Search Jobs', items, removeNull=True, headerTransform=pascalToSpace,
                                        headers=['id', 'status', 'user', 'query', 'timeCreated', 'timeCompleted']),
        raw_response=response,
    )


def get_job_command(client: Client, args: dict) -> CommandResults:
    job_id = args.get('id', '')
    response = client.get_job(job_id)
    items = to_items(response)
    return CommandResults(
        outputs_prefix='CriblSearch.Job',
        outputs_key_field='id',
        outputs=items,
        readable_output=tableToMarkdown(f'Cribl Search Job: {job_id}', items, removeNull=True,
                                        headerTransform=pascalToSpace),
        raw_response=response,
    )


def create_job_command(client: Client, args: dict) -> CommandResults:
    body = assign_params(
        query=args.get('query'),
        earliest=args.get('earliest'),
        latest=args.get('latest'),
        sampleRate=arg_to_number(args.get('sample_rate')),
        timezone=args.get('timezone'),
        isPrivate=arg_to_boolean(args.get('is_private')) if args.get('is_private') else None,
        numEventsBefore=arg_to_number(args.get('num_events_before')),
        numEventsAfter=arg_to_number(args.get('num_events_after')),
        targetEventTime=arg_to_number(args.get('target_event_time')),
        expectedOutputType=args.get('expected_output_type'),
    )
    set_options = parse_json_arg(args.get('set_options'), 'set_options')
    if set_options:
        body['setOptions'] = set_options
    if not body.get('query'):
        raise DemistoException('The "query" argument is required.')

    response = client.create_job(body)
    items = to_items(response)
    return CommandResults(
        outputs_prefix='CriblSearch.Job',
        outputs_key_field='id',
        outputs=items,
        readable_output=tableToMarkdown('Cribl Search Job Created', items, removeNull=True, headerTransform=pascalToSpace,
                                        headers=['id', 'status', 'query', 'earliest', 'latest', 'timeCreated']),
        raw_response=response,
    )


def update_job_command(client: Client, args: dict) -> CommandResults:
    job_id = args.get('id', '')
    body = assign_params(
        status=args.get('status'),
        isPrivate=arg_to_boolean(args.get('is_private')) if args.get('is_private') else None,
    )
    response = client.update_job(job_id, body)
    items = to_items(response)
    return CommandResults(
        outputs_prefix='CriblSearch.Job',
        outputs_key_field='id',
        outputs=items,
        readable_output=tableToMarkdown(f'Cribl Search Job Updated: {job_id}', items, removeNull=True,
                                        headerTransform=pascalToSpace),
        raw_response=response,
    )


def delete_job_command(client: Client, args: dict) -> CommandResults:
    job_id = args.get('id', '')
    client.delete_job(job_id)
    return CommandResults(readable_output=f'Cribl Search job {job_id} was deleted.')


def cancel_job_command(client: Client, args: dict) -> CommandResults:
    job_id = args.get('id', '')
    response = client.cancel_job(job_id)
    items = to_items(response)
    return CommandResults(
        outputs_prefix='CriblSearch.Job',
        outputs_key_field='id',
        outputs=items,
        readable_output=tableToMarkdown(f'Cribl Search Job Cancelled: {job_id}', items, removeNull=True,
                                        headerTransform=pascalToSpace, headers=['id', 'status', 'timeCompleted']),
        raw_response=response,
    )


def get_job_status_command(client: Client, args: dict) -> CommandResults:
    job_id = args.get('id', '')
    advanced = arg_to_boolean(args.get('advanced')) if args.get('advanced') else None
    response = client.get_job_status(job_id, advanced)
    status = response if isinstance(response, dict) else {}
    status = {**status, 'jobId': job_id}
    return CommandResults(
        outputs_prefix='CriblSearch.JobStatus',
        outputs_key_field='jobId',
        outputs=status,
        readable_output=tableToMarkdown(f'Cribl Search Job Status: {job_id}', status, removeNull=True,
                                        headerTransform=pascalToSpace,
                                        headers=['jobId', 'status', 'eventsFound', 'objectsSearched', 'objectsFound',
                                                 'bytesIn', 'timeStarted', 'timeCompleted']),
        raw_response=response,
    )


def _job_results(client: Client, args: dict, poll: bool) -> CommandResults:
    job_id = args.get('id', '')
    params = assign_params(
        limit=arg_to_number(args.get('limit')),
        offset=arg_to_number(args.get('offset')),
        lowerBound=arg_to_number(args.get('lower_bound')),
        upperBound=arg_to_number(args.get('upper_bound')),
    )
    if poll:
        params = assign_params(**params, lastJobStatus=args.get('last_job_status'))
        raw = client.get_job_results_poll(job_id, params)
    else:
        raw = client.get_job_results(job_id, params)

    summary, events = parse_ndjson(raw)
    outputs = {
        'jobId': job_id,
        'isFinished': summary.get('isFinished'),
        'totalEventCount': summary.get('totalEventCount'),
        'persistedEventCount': summary.get('persistedEventCount'),
        'offset': summary.get('offset'),
        'limit': summary.get('limit'),
        'events': events,
    }
    return CommandResults(
        outputs_prefix='CriblSearch.SearchResult',
        outputs_key_field='jobId',
        outputs=remove_empty_elements(outputs),
        readable_output=tableToMarkdown(
            f'Cribl Search Results: {job_id} ({len(events)} events shown, '
            f'{summary.get("totalEventCount", "?")} total)',
            events, removeNull=True),
        raw_response={'summary': summary, 'events': events},
    )


def get_job_results_command(client: Client, args: dict) -> CommandResults:
    return _job_results(client, args, poll=False)


def get_job_results_poll_command(client: Client, args: dict) -> CommandResults:
    return _job_results(client, args, poll=True)


def get_job_metrics_command(client: Client, args: dict) -> CommandResults:
    job_id = args.get('id', '')
    response = client.get_job_metrics(job_id)
    metrics = response.get('metrics', response) if isinstance(response, dict) else response
    outputs = {'jobId': job_id, 'metrics': metrics}
    return CommandResults(
        outputs_prefix='CriblSearch.JobMetrics',
        outputs_key_field='jobId',
        outputs=outputs,
        readable_output=tableToMarkdown(f'Cribl Search Job Metrics: {job_id}', metrics, removeNull=True,
                                        headerTransform=pascalToSpace),
        raw_response=response,
    )


def get_job_timeline_command(client: Client, args: dict) -> CommandResults:
    job_id = args.get('id', '')
    response = client.get_job_timeline(job_id)
    buckets = response.get('buckets', []) if isinstance(response, dict) else []
    outputs = {
        'jobId': job_id,
        'totalEventCount': response.get('totalEventCount') if isinstance(response, dict) else None,
        'buckets': buckets,
    }
    return CommandResults(
        outputs_prefix='CriblSearch.JobTimeline',
        outputs_key_field='jobId',
        outputs=remove_empty_elements(outputs),
        readable_output=tableToMarkdown(f'Cribl Search Job Timeline: {job_id}', buckets, removeNull=True,
                                        headerTransform=pascalToSpace),
        raw_response=response,
    )


def get_job_field_summaries_command(client: Client, args: dict) -> CommandResults:
    job_id = args.get('id', '')
    params = assign_params(limit=arg_to_number(args.get('limit')), offset=arg_to_number(args.get('offset')))
    response = client.get_job_field_summaries(job_id, params)
    fields = response.get('fields', []) if isinstance(response, dict) else []
    outputs = {
        'jobId': job_id,
        'totalEventCount': response.get('totalEventCount') if isinstance(response, dict) else None,
        'partial': response.get('partial') if isinstance(response, dict) else None,
        'fields': fields,
    }
    return CommandResults(
        outputs_prefix='CriblSearch.JobFieldSummary',
        outputs_key_field='jobId',
        outputs=remove_empty_elements(outputs),
        readable_output=tableToMarkdown(f'Cribl Search Job Field Summaries: {job_id}', fields, removeNull=True,
                                        headerTransform=pascalToSpace),
        raw_response=response,
    )


def list_job_logs_command(client: Client, args: dict) -> CommandResults:
    job_id = args.get('id', '')
    params = assign_params(limit=arg_to_number(args.get('limit')), offset=arg_to_number(args.get('offset')))
    response = client.list_job_logs(job_id, params)
    filenames = to_items(response)
    outputs = {'jobId': job_id, 'logFiles': filenames}
    return CommandResults(
        outputs_prefix='CriblSearch.JobLog',
        outputs_key_field='jobId',
        outputs=outputs,
        readable_output=tableToMarkdown(f'Cribl Search Job Log Files: {job_id}', [{'filename': f} for f in filenames],
                                        removeNull=True),
        raw_response=response,
    )


def get_job_settings_command(client: Client, args: dict) -> CommandResults:
    job_id = args.get('id', '')
    response = client.get_job_settings(job_id)
    outputs = {**(response if isinstance(response, dict) else {}), 'jobId': job_id}
    return CommandResults(
        outputs_prefix='CriblSearch.JobSettings',
        outputs_key_field='jobId',
        outputs=outputs,
        readable_output=tableToMarkdown(f'Cribl Search Job Settings: {job_id}', outputs, removeNull=True,
                                        headerTransform=pascalToSpace),
        raw_response=response,
    )


def update_job_settings_command(client: Client, args: dict) -> CommandResults:
    job_id = args.get('id', '')
    body = assign_params(reaperKeepUntil=arg_to_number(args.get('reaper_keep_until')))
    response = client.update_job_settings(job_id, body)
    outputs = {**(response if isinstance(response, dict) else {}), 'jobId': job_id}
    return CommandResults(
        outputs_prefix='CriblSearch.JobSettings',
        outputs_key_field='jobId',
        outputs=outputs,
        readable_output=tableToMarkdown(f'Cribl Search Job Settings Updated: {job_id}', outputs, removeNull=True,
                                        headerTransform=pascalToSpace),
        raw_response=response,
    )


""" COMMAND FUNCTIONS - SAVED SEARCHES """


def list_saved_searches_command(client: Client, args: dict) -> CommandResults:
    params = assign_params(
        limit=arg_to_number(args.get('limit')),
        offset=arg_to_number(args.get('offset')),
        output=args.get('output'),
        resolveDatasets=arg_to_boolean(args.get('resolve_datasets')) if args.get('resolve_datasets') else None,
        datasetIds=argToList(args.get('dataset_ids')) or None,
    )
    response = client.list_saved_searches(params)
    items = to_items(response)
    return CommandResults(
        outputs_prefix='CriblSearch.SavedSearch',
        outputs_key_field='id',
        outputs=items,
        readable_output=tableToMarkdown('Cribl Saved Searches', items, removeNull=True, headerTransform=pascalToSpace,
                                        headers=['id', 'name', 'description', 'query', 'user', 'isPrivate']),
        raw_response=response,
    )


def get_saved_search_command(client: Client, args: dict) -> CommandResults:
    saved_id = args.get('id', '')
    response = client.get_saved_search(saved_id)
    items = to_items(response)
    return CommandResults(
        outputs_prefix='CriblSearch.SavedSearch',
        outputs_key_field='id',
        outputs=items,
        readable_output=tableToMarkdown(f'Cribl Saved Search: {saved_id}', items, removeNull=True,
                                        headerTransform=pascalToSpace),
        raw_response=response,
    )


def _saved_search_body(args: dict) -> dict:
    body = parse_json_arg(args.get('body'), 'body')
    body.update(assign_params(
        id=args.get('id'),
        name=args.get('name'),
        query=args.get('query'),
        description=args.get('description'),
        earliest=args.get('earliest'),
        latest=args.get('latest'),
        sampleRate=arg_to_number(args.get('sample_rate')),
        timezone=args.get('timezone'),
        isPrivate=arg_to_boolean(args.get('is_private')) if args.get('is_private') else None,
    ))
    schedule = parse_json_arg(args.get('schedule'), 'schedule')
    if schedule:
        body['schedule'] = schedule
    return body


def create_saved_search_command(client: Client, args: dict) -> CommandResults:
    body = _saved_search_body(args)
    for required in ('id', 'name', 'query'):
        if not body.get(required):
            raise DemistoException(f'The "{required}" argument is required to create a saved search.')
    response = client.create_saved_search(body)
    items = to_items(response)
    return CommandResults(
        outputs_prefix='CriblSearch.SavedSearch',
        outputs_key_field='id',
        outputs=items,
        readable_output=tableToMarkdown('Cribl Saved Search Created', items, removeNull=True,
                                        headerTransform=pascalToSpace, headers=['id', 'name', 'query', 'description']),
        raw_response=response,
    )


def update_saved_search_command(client: Client, args: dict) -> CommandResults:
    saved_id = args.get('id', '')
    body = _saved_search_body(args)
    body.setdefault('id', saved_id)
    response = client.update_saved_search(saved_id, body)
    items = to_items(response)
    return CommandResults(
        outputs_prefix='CriblSearch.SavedSearch',
        outputs_key_field='id',
        outputs=items,
        readable_output=tableToMarkdown(f'Cribl Saved Search Updated: {saved_id}', items, removeNull=True,
                                        headerTransform=pascalToSpace),
        raw_response=response,
    )


def delete_saved_search_command(client: Client, args: dict) -> CommandResults:
    saved_id = args.get('id', '')
    client.delete_saved_search(saved_id)
    return CommandResults(readable_output=f'Cribl saved search {saved_id} was deleted.')


""" COMMAND FUNCTIONS - DATASETS """


def list_datasets_command(client: Client, args: dict) -> CommandResults:
    params = assign_params(
        limit=arg_to_number(args.get('limit')),
        offset=arg_to_number(args.get('offset')),
        explorerStats=arg_to_boolean(args.get('explorer_stats')) if args.get('explorer_stats') else None,
        lastUsed=arg_to_boolean(args.get('last_used')) if args.get('last_used') else None,
        favorites=arg_to_boolean(args.get('favorites')) if args.get('favorites') else None,
        vtables=arg_to_boolean(args.get('vtables')) if args.get('vtables') else None,
    )
    response = client.list_datasets(params)
    items = to_items(response)
    return CommandResults(
        outputs_prefix='CriblSearch.Dataset',
        outputs_key_field='id',
        outputs=items,
        readable_output=tableToMarkdown('Cribl Search Datasets', items, removeNull=True, headerTransform=pascalToSpace,
                                        headers=['id', 'type', 'description', 'provider', 'providerType']),
        raw_response=response,
    )


def get_dataset_command(client: Client, args: dict) -> CommandResults:
    dataset_id = args.get('id', '')
    response = client.get_dataset(dataset_id)
    items = to_items(response)
    return CommandResults(
        outputs_prefix='CriblSearch.Dataset',
        outputs_key_field='id',
        outputs=items,
        readable_output=tableToMarkdown(f'Cribl Search Dataset: {dataset_id}', items, removeNull=True,
                                        headerTransform=pascalToSpace),
        raw_response=response,
    )


def create_dataset_command(client: Client, args: dict) -> CommandResults:
    body = parse_json_arg(args.get('body'), 'body')
    if not body:
        raise DemistoException('The "body" argument (JSON) is required to create a dataset.')
    response = client.create_dataset(body)
    items = to_items(response)
    return CommandResults(
        outputs_prefix='CriblSearch.Dataset',
        outputs_key_field='id',
        outputs=items,
        readable_output=tableToMarkdown('Cribl Search Dataset Created', items, removeNull=True,
                                        headerTransform=pascalToSpace, headers=['id', 'type', 'description']),
        raw_response=response,
    )


def update_dataset_command(client: Client, args: dict) -> CommandResults:
    dataset_id = args.get('id', '')
    body = parse_json_arg(args.get('body'), 'body')
    if not body:
        raise DemistoException('The "body" argument (JSON) is required to update a dataset.')
    response = client.update_dataset(dataset_id, body)
    items = to_items(response)
    return CommandResults(
        outputs_prefix='CriblSearch.Dataset',
        outputs_key_field='id',
        outputs=items,
        readable_output=tableToMarkdown(f'Cribl Search Dataset Updated: {dataset_id}', items, removeNull=True,
                                        headerTransform=pascalToSpace),
        raw_response=response,
    )


def delete_dataset_command(client: Client, args: dict) -> CommandResults:
    dataset_id = args.get('id', '')
    client.delete_dataset(dataset_id)
    return CommandResults(readable_output=f'Cribl Search dataset {dataset_id} was deleted.')


def delete_dataset_data_command(client: Client, args: dict) -> CommandResults:
    dataset_id = args.get('id', '')
    client.delete_dataset_data(dataset_id)
    return CommandResults(readable_output=f'Ingested events were removed from Cribl Search dataset {dataset_id}.')


def get_dataset_fields_command(client: Client, args: dict) -> CommandResults:
    dataset_id = args.get('id', '')
    start_ms, end_ms, granularity_ms = resolve_stats_window(args)
    params = assign_params(
        startTime=start_ms, endTime=end_ms, granularity=granularity_ms,
        topValues=arg_to_boolean(args.get('top_values')) if args.get('top_values') else None,
    )
    response = client.get_dataset_fields(dataset_id, params)
    fields = response.get('fields', []) if isinstance(response, dict) else []
    outputs = {
        'datasetId': dataset_id,
        'fields': fields,
        'topValues': response.get('topValues') if isinstance(response, dict) else None,
    }
    return CommandResults(
        outputs_prefix='CriblSearch.DatasetField',
        outputs_key_field='datasetId',
        outputs=remove_empty_elements(outputs),
        readable_output=tableToMarkdown(f'Cribl Search Dataset Fields: {dataset_id}',
                                        [{'field': f} for f in fields], removeNull=True),
        raw_response=response,
    )


def _dataset_stats(client: Client, args: dict, fetch_fn, prefix: str, title: str) -> CommandResults:
    dataset_id = args.get('id', '')
    start_ms, end_ms, granularity_ms = resolve_stats_window(args)
    params = assign_params(startTime=start_ms, endTime=end_ms, granularity=granularity_ms)
    response = fetch_fn(dataset_id, params)
    outputs = {**(response if isinstance(response, dict) else {'value': response}), 'datasetId': dataset_id}
    return CommandResults(
        outputs_prefix=prefix,
        outputs_key_field='datasetId',
        outputs=outputs,
        readable_output=tableToMarkdown(f'{title}: {dataset_id}', outputs, removeNull=True,
                                        headerTransform=pascalToSpace),
        raw_response=response,
    )


def get_dataset_stats_command(client: Client, args: dict) -> CommandResults:
    return _dataset_stats(client, args, client.get_dataset_stats,
                          'CriblSearch.DatasetStats', 'Cribl Search Dataset Statistics')


def get_dataset_field_stats_command(client: Client, args: dict) -> CommandResults:
    dataset_id = args.get('id', '')
    start_ms, end_ms, granularity_ms = resolve_stats_window(args)
    params = assign_params(
        startTime=start_ms, endTime=end_ms, granularity=granularity_ms,
        limit=arg_to_number(args.get('limit')), offset=arg_to_number(args.get('offset')),
        sort=args.get('sort'), filter=args.get('filter'),
    )
    response = client.get_dataset_field_stats(dataset_id, params)
    field_stats = response.get('fieldStats', []) if isinstance(response, dict) else []
    outputs = {
        'datasetId': dataset_id,
        'totalEventCount': response.get('totalEventCount') if isinstance(response, dict) else None,
        'totalFieldCount': response.get('totalFieldCount') if isinstance(response, dict) else None,
        'fieldStats': field_stats,
    }
    return CommandResults(
        outputs_prefix='CriblSearch.DatasetFieldStats',
        outputs_key_field='datasetId',
        outputs=remove_empty_elements(outputs),
        readable_output=tableToMarkdown(f'Cribl Search Dataset Field Statistics: {dataset_id}', field_stats,
                                        removeNull=True, headerTransform=pascalToSpace),
        raw_response=response,
    )


def get_dataset_dimension_stats_command(client: Client, args: dict) -> CommandResults:
    dataset_id = args.get('id', '')
    start_ms, end_ms, granularity_ms = resolve_stats_window(args)
    params = assign_params(
        startTime=start_ms, endTime=end_ms, granularity=granularity_ms,
        metricName=args.get('metric_name'),
        limit=arg_to_number(args.get('limit')),
        topValuesLimit=arg_to_number(args.get('top_values_limit')),
    )
    response = client.get_dataset_dimension_stats(dataset_id, params)
    dim_stats = response.get('dimensionStats', []) if isinstance(response, dict) else []
    outputs = {
        'datasetId': dataset_id,
        'totalSampleCount': response.get('totalSampleCount') if isinstance(response, dict) else None,
        'totalSeriesCount': response.get('totalSeriesCount') if isinstance(response, dict) else None,
        'dimensionStats': dim_stats,
    }
    return CommandResults(
        outputs_prefix='CriblSearch.DatasetDimensionStats',
        outputs_key_field='datasetId',
        outputs=remove_empty_elements(outputs),
        readable_output=tableToMarkdown(f'Cribl Search Dataset Dimension Statistics: {dataset_id}', dim_stats,
                                        removeNull=True, headerTransform=pascalToSpace),
        raw_response=response,
    )


def get_dataset_usage_stats_command(client: Client, args: dict) -> CommandResults:
    dataset_id = args.get('id', '')
    end_dt = arg_to_datetime(args.get('end_time'))
    end_ms = int(end_dt.timestamp() * 1000) if end_dt else None
    params = assign_params(
        endTime=end_ms,
        timeWindow=arg_to_number(args.get('time_window')),
        granularity=arg_to_number(args.get('granularity')),
    )
    response = client.get_dataset_usage_stats(dataset_id, params)
    outputs = {**(response if isinstance(response, dict) else {}), 'datasetId': dataset_id}
    return CommandResults(
        outputs_prefix='CriblSearch.DatasetUsageStats',
        outputs_key_field='datasetId',
        outputs=outputs,
        readable_output=tableToMarkdown(f'Cribl Search Dataset Usage Statistics: {dataset_id}',
                                        outputs.get('topUsers', []), removeNull=True, headerTransform=pascalToSpace),
        raw_response=response,
    )


""" COMMAND FUNCTIONS - DATASET PROVIDERS """


def list_dataset_providers_command(client: Client, args: dict) -> CommandResults:
    params = assign_params(limit=arg_to_number(args.get('limit')), offset=arg_to_number(args.get('offset')))
    response = client.list_dataset_providers(params)
    items = to_items(response)
    return CommandResults(
        outputs_prefix='CriblSearch.DatasetProvider',
        outputs_key_field='id',
        outputs=items,
        readable_output=tableToMarkdown('Cribl Search Dataset Providers', items, removeNull=True,
                                        headerTransform=pascalToSpace, headers=['id', 'type', 'description']),
        raw_response=response,
    )


def get_dataset_provider_command(client: Client, args: dict) -> CommandResults:
    provider_id = args.get('id', '')
    response = client.get_dataset_provider(provider_id)
    items = to_items(response)
    return CommandResults(
        outputs_prefix='CriblSearch.DatasetProvider',
        outputs_key_field='id',
        outputs=items,
        readable_output=tableToMarkdown(f'Cribl Search Dataset Provider: {provider_id}', items, removeNull=True,
                                        headerTransform=pascalToSpace),
        raw_response=response,
    )


def create_dataset_provider_command(client: Client, args: dict) -> CommandResults:
    body = parse_json_arg(args.get('body'), 'body')
    if not body:
        raise DemistoException('The "body" argument (JSON) is required to create a dataset provider.')
    response = client.create_dataset_provider(body)
    items = to_items(response)
    return CommandResults(
        outputs_prefix='CriblSearch.DatasetProvider',
        outputs_key_field='id',
        outputs=items,
        readable_output=tableToMarkdown('Cribl Search Dataset Provider Created', items, removeNull=True,
                                        headerTransform=pascalToSpace, headers=['id', 'type', 'description']),
        raw_response=response,
    )


def update_dataset_provider_command(client: Client, args: dict) -> CommandResults:
    provider_id = args.get('id', '')
    body = parse_json_arg(args.get('body'), 'body')
    if not body:
        raise DemistoException('The "body" argument (JSON) is required to update a dataset provider.')
    response = client.update_dataset_provider(provider_id, body)
    items = to_items(response)
    return CommandResults(
        outputs_prefix='CriblSearch.DatasetProvider',
        outputs_key_field='id',
        outputs=items,
        readable_output=tableToMarkdown(f'Cribl Search Dataset Provider Updated: {provider_id}', items, removeNull=True,
                                        headerTransform=pascalToSpace),
        raw_response=response,
    )


def delete_dataset_provider_command(client: Client, args: dict) -> CommandResults:
    provider_id = args.get('id', '')
    client.delete_dataset_provider(provider_id)
    return CommandResults(readable_output=f'Cribl Search dataset provider {provider_id} was deleted.')


def get_dataset_provider_details_command(client: Client, args: dict) -> CommandResults:
    provider_id = args.get('id', '')
    response = client.get_dataset_provider_details(provider_id)
    outputs = {**(response if isinstance(response, dict) else {}), 'id': provider_id}
    return CommandResults(
        outputs_prefix='CriblSearch.DatasetProviderDetails',
        outputs_key_field='id',
        outputs=outputs,
        readable_output=tableToMarkdown(f'Cribl Search Dataset Provider Discovery: {provider_id}', outputs,
                                        removeNull=True, headerTransform=pascalToSpace),
        raw_response=response,
    )


def list_dataset_provider_types_command(client: Client, args: dict) -> CommandResults:
    params = assign_params(limit=arg_to_number(args.get('limit')), offset=arg_to_number(args.get('offset')))
    response = client.list_dataset_provider_types(params)
    items = to_items(response)
    return CommandResults(
        outputs_prefix='CriblSearch.DatasetProviderType',
        outputs_key_field='id',
        outputs=items,
        readable_output=tableToMarkdown('Cribl Search Dataset Provider Types', items, removeNull=True,
                                        headerTransform=pascalToSpace, headers=['id', 'description', 'capabilities']),
        raw_response=response,
    )


def get_dataset_provider_type_command(client: Client, args: dict) -> CommandResults:
    type_id = args.get('id', '')
    response = client.get_dataset_provider_type(type_id)
    items = to_items(response)
    return CommandResults(
        outputs_prefix='CriblSearch.DatasetProviderType',
        outputs_key_field='id',
        outputs=items,
        readable_output=tableToMarkdown(f'Cribl Search Dataset Provider Type: {type_id}', items, removeNull=True,
                                        headerTransform=pascalToSpace),
        raw_response=response,
    )


""" COMMAND FUNCTIONS - MACROS """


def list_macros_command(client: Client, args: dict) -> CommandResults:
    params = assign_params(limit=arg_to_number(args.get('limit')), offset=arg_to_number(args.get('offset')))
    response = client.list_macros(params)
    items = to_items(response)
    return CommandResults(
        outputs_prefix='CriblSearch.Macro',
        outputs_key_field='id',
        outputs=items,
        readable_output=tableToMarkdown('Cribl Search Macros', items, removeNull=True, headerTransform=pascalToSpace,
                                        headers=['id', 'description', 'replacement', 'tags']),
        raw_response=response,
    )


def get_macro_command(client: Client, args: dict) -> CommandResults:
    macro_id = args.get('id', '')
    response = client.get_macro(macro_id)
    items = to_items(response)
    return CommandResults(
        outputs_prefix='CriblSearch.Macro',
        outputs_key_field='id',
        outputs=items,
        readable_output=tableToMarkdown(f'Cribl Search Macro: {macro_id}', items, removeNull=True,
                                        headerTransform=pascalToSpace),
        raw_response=response,
    )


def create_macro_command(client: Client, args: dict) -> CommandResults:
    body = assign_params(
        id=args.get('id'),
        replacement=args.get('replacement'),
        description=args.get('description'),
        tags=args.get('tags'),
    )
    for required in ('id', 'replacement'):
        if not body.get(required):
            raise DemistoException(f'The "{required}" argument is required to create a macro.')
    response = client.create_macro(body)
    items = to_items(response)
    return CommandResults(
        outputs_prefix='CriblSearch.Macro',
        outputs_key_field='id',
        outputs=items,
        readable_output=tableToMarkdown('Cribl Search Macro Created', items, removeNull=True,
                                        headerTransform=pascalToSpace, headers=['id', 'replacement', 'description']),
        raw_response=response,
    )


def update_macro_command(client: Client, args: dict) -> CommandResults:
    macro_id = args.get('id', '')
    body = assign_params(
        id=macro_id,
        replacement=args.get('replacement'),
        description=args.get('description'),
        tags=args.get('tags'),
    )
    response = client.update_macro(macro_id, body)
    items = to_items(response)
    return CommandResults(
        outputs_prefix='CriblSearch.Macro',
        outputs_key_field='id',
        outputs=items,
        readable_output=tableToMarkdown(f'Cribl Search Macro Updated: {macro_id}', items, removeNull=True,
                                        headerTransform=pascalToSpace),
        raw_response=response,
    )


def delete_macro_command(client: Client, args: dict) -> CommandResults:
    macro_id = args.get('id', '')
    client.delete_macro(macro_id)
    return CommandResults(readable_output=f'Cribl Search macro {macro_id} was deleted.')


""" COMMAND FUNCTIONS - DATATYPES """


def list_datatypes_command(client: Client, args: dict) -> CommandResults:
    params = assign_params(limit=arg_to_number(args.get('limit')), offset=arg_to_number(args.get('offset')))
    response = client.list_datatypes(params)
    items = to_items(response)
    return CommandResults(
        outputs_prefix='CriblSearch.Datatype',
        outputs_key_field='id',
        outputs=items,
        readable_output=tableToMarkdown('Cribl Search Datatypes', items, removeNull=True, headerTransform=pascalToSpace,
                                        headers=['id', 'description', 'dataFormat', 'lib', 'tags']),
        raw_response=response,
    )


def get_datatype_command(client: Client, args: dict) -> CommandResults:
    datatype_id = args.get('id', '')
    response = client.get_datatype(datatype_id)
    items = to_items(response)
    return CommandResults(
        outputs_prefix='CriblSearch.Datatype',
        outputs_key_field='id',
        outputs=items,
        readable_output=tableToMarkdown(f'Cribl Search Datatype: {datatype_id}', items, removeNull=True,
                                        headerTransform=pascalToSpace),
        raw_response=response,
    )


def create_datatype_command(client: Client, args: dict) -> CommandResults:
    body = parse_json_arg(args.get('body'), 'body')
    if not body:
        raise DemistoException('The "body" argument (JSON) is required to create a datatype.')
    response = client.create_datatype(body)
    items = to_items(response)
    return CommandResults(
        outputs_prefix='CriblSearch.Datatype',
        outputs_key_field='id',
        outputs=items,
        readable_output=tableToMarkdown('Cribl Search Datatype Created', items, removeNull=True,
                                        headerTransform=pascalToSpace, headers=['id', 'dataFormat', 'description']),
        raw_response=response,
    )


def update_datatype_command(client: Client, args: dict) -> CommandResults:
    datatype_id = args.get('id', '')
    body = parse_json_arg(args.get('body'), 'body')
    if not body:
        raise DemistoException('The "body" argument (JSON) is required to update a datatype.')
    response = client.update_datatype(datatype_id, body)
    items = to_items(response)
    return CommandResults(
        outputs_prefix='CriblSearch.Datatype',
        outputs_key_field='id',
        outputs=items,
        readable_output=tableToMarkdown(f'Cribl Search Datatype Updated: {datatype_id}', items, removeNull=True,
                                        headerTransform=pascalToSpace),
        raw_response=response,
    )


def delete_datatype_command(client: Client, args: dict) -> CommandResults:
    datatype_id = args.get('id', '')
    client.delete_datatype(datatype_id)
    return CommandResults(readable_output=f'Cribl Search datatype {datatype_id} was deleted.')


""" MAIN """


def main() -> None:
    params = demisto.params()
    args = demisto.args()
    command = demisto.command()

    base_url = params.get('url', '').rstrip('/')
    client_id = (params.get('credentials') or {}).get('identifier', '')
    client_secret = (params.get('credentials') or {}).get('password', '')
    token_url = params.get('token_url') or CRIBL_CLOUD_TOKEN_URL
    verify_certificate = not params.get('insecure', False)
    proxy = params.get('proxy', False)

    demisto.debug(f'Command being called is {command}')

    try:
        # Thin client used only for token operations — no auth header needed
        # since the token endpoint authenticates via the request body.
        auth_client = Client(
            base_url=base_url,
            api_key='',
            verify=verify_certificate,
            proxy=proxy,
        )

        if command == 'test-module':
            return_results(test_module(auth_client, client_id, client_secret, token_url,
                                       base_url, verify_certificate, proxy))
            return

        token = get_valid_token(auth_client, client_id, client_secret, token_url)
        client = Client(
            base_url=base_url,
            api_key=token,
            verify=verify_certificate,
            proxy=proxy,
        )

        commands = {
            # Search Jobs
            'Cribl-search-list-jobs': list_jobs_command,
            'Cribl-search-get-job': get_job_command,
            'Cribl-search-create-job': create_job_command,
            'Cribl-search-update-job': update_job_command,
            'Cribl-search-delete-job': delete_job_command,
            'Cribl-search-cancel-job': cancel_job_command,
            'Cribl-search-get-job-status': get_job_status_command,
            'Cribl-search-get-job-results': get_job_results_command,
            'Cribl-search-get-job-results-poll': get_job_results_poll_command,
            'Cribl-search-get-job-metrics': get_job_metrics_command,
            'Cribl-search-get-job-timeline': get_job_timeline_command,
            'Cribl-search-get-job-field-summaries': get_job_field_summaries_command,
            'Cribl-search-list-job-logs': list_job_logs_command,
            'Cribl-search-get-job-settings': get_job_settings_command,
            'Cribl-search-update-job-settings': update_job_settings_command,
            # Saved Searches
            'Cribl-search-list-saved-searches': list_saved_searches_command,
            'Cribl-search-get-saved-search': get_saved_search_command,
            'Cribl-search-create-saved-search': create_saved_search_command,
            'Cribl-search-update-saved-search': update_saved_search_command,
            'Cribl-search-delete-saved-search': delete_saved_search_command,
            # Datasets
            'Cribl-search-list-datasets': list_datasets_command,
            'Cribl-search-get-dataset': get_dataset_command,
            'Cribl-search-create-dataset': create_dataset_command,
            'Cribl-search-update-dataset': update_dataset_command,
            'Cribl-search-delete-dataset': delete_dataset_command,
            'Cribl-search-delete-dataset-data': delete_dataset_data_command,
            'Cribl-search-get-dataset-fields': get_dataset_fields_command,
            'Cribl-search-get-dataset-stats': get_dataset_stats_command,
            'Cribl-search-get-dataset-field-stats': get_dataset_field_stats_command,
            'Cribl-search-get-dataset-dimension-stats': get_dataset_dimension_stats_command,
            'Cribl-search-get-dataset-usage-stats': get_dataset_usage_stats_command,
            # Dataset Providers
            'Cribl-search-list-dataset-providers': list_dataset_providers_command,
            'Cribl-search-get-dataset-provider': get_dataset_provider_command,
            'Cribl-search-create-dataset-provider': create_dataset_provider_command,
            'Cribl-search-update-dataset-provider': update_dataset_provider_command,
            'Cribl-search-delete-dataset-provider': delete_dataset_provider_command,
            'Cribl-search-get-dataset-provider-details': get_dataset_provider_details_command,
            'Cribl-search-list-dataset-provider-types': list_dataset_provider_types_command,
            'Cribl-search-get-dataset-provider-type': get_dataset_provider_type_command,
            # Macros
            'Cribl-search-list-macros': list_macros_command,
            'Cribl-search-get-macro': get_macro_command,
            'Cribl-search-create-macro': create_macro_command,
            'Cribl-search-update-macro': update_macro_command,
            'Cribl-search-delete-macro': delete_macro_command,
            # Datatypes
            'Cribl-search-list-datatypes': list_datatypes_command,
            'Cribl-search-get-datatype': get_datatype_command,
            'Cribl-search-create-datatype': create_datatype_command,
            'Cribl-search-update-datatype': update_datatype_command,
            'Cribl-search-delete-datatype': delete_datatype_command,
        }

        if command in commands:
            return_results(commands[command](client, args))
        else:
            raise NotImplementedError(f'Command {command} is not implemented')

    except Exception as e:
        return_error(f'Failed to execute {command} command.\nError:\n{str(e)}')


if __name__ in ('__main__', '__builtin__', 'builtins'):
    main()
