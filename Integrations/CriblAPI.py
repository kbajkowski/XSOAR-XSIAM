import json
import time

import demistomock as demisto  # noqa: F401
from CommonServerPython import *  # noqa: F401
from CommonServerUserPython import *  # noqa: F401

VENDOR_NAME = 'CriblAPI'
CRIBL_CLOUD_TOKEN_URL = 'https://login.cribl.cloud/oauth/token'
CRIBL_CLOUD_AUDIENCE = 'https://api.cribl.cloud'


""" HELPERS """


def is_token_expired(expiry_timestamp: int, buffer_seconds: int = 60) -> bool:
    return int(time.time()) >= (expiry_timestamp - buffer_seconds)


def create_expiry_timestamp(expires_in: int) -> int:
    return int(time.time()) + expires_in


def scoped_suffix(suffix: str, worker_group: str | None = None, worker_node: str | None = None) -> str:
    """Prepend w/{worker_node} or m/{worker_group} routing prefix when a scope is specified."""
    if worker_node:
        return f'w/{worker_node}/{suffix.lstrip("/")}'
    if worker_group:
        return f'm/{worker_group}/{suffix.lstrip("/")}'
    return suffix


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

    # --- System ---

    def get_system_info(self, fields: str | None, messages: bool | None, conf: bool | None) -> dict:
        params = assign_params(fields=fields, messages=messages, conf=conf)
        return self._http_request('GET', '/system/info', params=params)

    def get_health(self) -> dict:
        return self._http_request('GET', '/health', ok_codes=(200, 420))

    # --- Master Groups ---

    def list_master_groups(self, fields: str | None = None, product: str | None = None) -> dict:
        params = assign_params(fields=fields, product=product)
        return self._http_request('GET', '/master/groups', params=params)

    def get_master_group(self, group_id: str, fields: str | None = None) -> dict:
        params = assign_params(fields=fields)
        return self._http_request('GET', f'/master/groups/{group_id}', params=params)

    def update_master_group(self, group_id: str, body: dict) -> dict:
        return self._http_request('PATCH', f'/master/groups/{group_id}', json_data=body)

    def delete_master_group(self, group_id: str) -> dict:
        return self._http_request('DELETE', f'/master/groups/{group_id}')

    def deploy_master_group(self, group_id: str) -> dict:
        return self._http_request('PATCH', f'/master/groups/{group_id}/deploy', json_data={})

    def get_master_group_config_version(self, group_id: str) -> dict:
        return self._http_request('GET', f'/master/groups/{group_id}/configVersion')

    # --- Product Groups (newer non-deprecated API) ---

    def list_product_groups(self, product: str, fields: str | None = None) -> dict:
        params = assign_params(fields=fields)
        return self._http_request('GET', f'/products/{product}/groups', params=params)

    def get_product_group(self, product: str, group_id: str, fields: str | None = None) -> dict:
        params = assign_params(fields=fields)
        return self._http_request('GET', f'/products/{product}/groups/{group_id}', params=params)

    def deploy_product_group(self, product: str, group_id: str) -> dict:
        return self._http_request('PATCH', f'/products/{product}/groups/{group_id}/deploy', json_data={})

    # --- Workers ---

    def list_workers(self, product: str, limit: int | None, offset: int | None,
                     filter_exp: str | None = None) -> dict:
        params = assign_params(limit=limit, offset=offset, filterExp=filter_exp)
        return self._http_request('GET', f'/products/{product}/workers', params=params)

    def restart_workers(self, product: str) -> dict:
        return self._http_request('PATCH', f'/products/{product}/workers/restart', json_data={})

    # --- Pipelines ---

    def list_pipelines(self, worker_group: str | None = None, worker_node: str | None = None) -> dict:
        return self._http_request('GET', scoped_suffix('/pipelines', worker_group, worker_node))

    def get_pipeline(self, pipeline_id: str, worker_group: str | None = None,
                     worker_node: str | None = None) -> dict:
        return self._http_request('GET', scoped_suffix(f'/pipelines/{pipeline_id}', worker_group, worker_node))

    # --- Sources ---

    def list_sources(self, source_type: str | None = None, worker_group: str | None = None,
                     worker_node: str | None = None) -> dict:
        params = assign_params(type=source_type)
        return self._http_request('GET', scoped_suffix('/system/inputs', worker_group, worker_node), params=params)

    def get_source(self, source_id: str, worker_group: str | None = None,
                   worker_node: str | None = None) -> dict:
        return self._http_request('GET', scoped_suffix(f'/system/inputs/{source_id}', worker_group, worker_node))

    def list_source_status(self, metrics: bool | None = None, limit: int | None = None,
                           offset: int | None = None, worker_group: str | None = None,
                           worker_node: str | None = None) -> dict:
        params = assign_params(metrics=metrics, limit=limit, offset=offset)
        return self._http_request('GET', scoped_suffix('/system/status/inputs', worker_group, worker_node),
                                  params=params)

    def get_source_status(self, source_id: str, metrics: bool | None = None,
                          worker_group: str | None = None, worker_node: str | None = None) -> dict:
        params = assign_params(metrics=metrics)
        return self._http_request('GET',
                                  scoped_suffix(f'/system/status/inputs/{source_id}', worker_group, worker_node),
                                  params=params)

    # --- Destinations ---

    def list_destinations(self, dest_type: str | None = None, worker_group: str | None = None,
                          worker_node: str | None = None) -> dict:
        params = assign_params(type=dest_type)
        return self._http_request('GET', scoped_suffix('/system/outputs', worker_group, worker_node), params=params)

    def get_destination(self, dest_id: str, worker_group: str | None = None,
                        worker_node: str | None = None) -> dict:
        return self._http_request('GET', scoped_suffix(f'/system/outputs/{dest_id}', worker_group, worker_node))

    def list_destination_status(self, metrics: bool | None = None, limit: int | None = None,
                                offset: int | None = None, worker_group: str | None = None,
                                worker_node: str | None = None) -> dict:
        params = assign_params(metrics=metrics, limit=limit, offset=offset)
        return self._http_request('GET', scoped_suffix('/system/status/outputs', worker_group, worker_node),
                                  params=params)

    def get_destination_status(self, dest_id: str, metrics: bool | None = None,
                               worker_group: str | None = None, worker_node: str | None = None) -> dict:
        params = assign_params(metrics=metrics)
        return self._http_request('GET',
                                  scoped_suffix(f'/system/status/outputs/{dest_id}', worker_group, worker_node),
                                  params=params)

    # --- Jobs ---

    def list_jobs(self, limit: int | None, offset: int | None, run_type: str | None,
                  state: str | None, collector_id: str | None) -> dict:
        params = assign_params(limit=limit, offset=offset, runType=run_type, state=state, collectorId=collector_id)
        return self._http_request('GET', '/jobs', params=params)

    def get_job(self, job_id: str) -> dict:
        return self._http_request('GET', f'/jobs/{job_id}')

    def cancel_job(self, job_id: str) -> dict:
        return self._http_request('PATCH', f'/jobs/{job_id}/cancel')

    def pause_job(self, job_id: str) -> dict:
        return self._http_request('PATCH', f'/jobs/{job_id}/pause')

    def resume_job(self, job_id: str) -> dict:
        return self._http_request('PATCH', f'/jobs/{job_id}/resume')

    # --- Lookups ---

    def list_lookups(self) -> dict:
        return self._http_request('GET', '/system/lookups')

    def get_lookup(self, lookup_id: str) -> dict:
        return self._http_request('GET', f'/system/lookups/{lookup_id}')

    # --- Metrics ---

    def query_metrics(self, body: dict) -> dict:
        return self._http_request('POST', '/system/metrics/query', json_data=body)


""" TOKEN MANAGEMENT """


def get_valid_token(auth_client: 'Client', client_id: str, client_secret: str, token_url: str) -> str:
    """Return a cached token, refreshing via OAuth2 if expired or absent."""
    ctx = get_integration_context()
    token = ctx.get('token')
    expiry = ctx.get('expiry')

    if not token or not expiry or is_token_expired(expiry):
        demisto.debug('CriblAPI: token missing or expired, fetching new token')
        token_data = auth_client.get_token(client_id, client_secret, token_url)
        token = token_data.get('access_token')
        if not token:
            raise DemistoException('Failed to obtain access_token from Cribl Cloud. Check client_id and client_secret.')
        expiry = create_expiry_timestamp(token_data.get('expires_in', 3600))
        set_integration_context({'token': token, 'expiry': expiry})

    return token


""" TEST MODULE """


def test_module(auth_client: 'Client', client_id: str, client_secret: str, token_url: str) -> str:
    try:
        token_data = auth_client.get_token(client_id, client_secret, token_url)
        if not token_data.get('access_token'):
            return 'Authorization Error: no access_token in response. Check client_id and client_secret.'
        return 'ok'
    except DemistoException as e:
        if '401' in str(e) or 'Unauthorized' in str(e) or 'access_denied' in str(e):
            return 'Authorization Error: make sure client_id and client_secret are correct.'
        raise


""" COMMAND FUNCTIONS """


def get_system_info_command(client: Client, args: dict) -> CommandResults:
    fields = args.get('fields')
    messages = arg_to_boolean(args.get('messages')) if args.get('messages') else None
    conf = arg_to_boolean(args.get('conf')) if args.get('conf') else None
    response = client.get_system_info(fields, messages, conf)
    items = response.get('items', [response])
    return CommandResults(
        outputs_prefix='CriblAPI.SystemInfo',
        outputs_key_field='guid',
        outputs=items,
        readable_output=tableToMarkdown('Cribl System Info', items, removeNull=True, headerTransform=pascalToSpace),
        raw_response=response,
    )


def get_health_command(client: Client, args: dict) -> CommandResults:
    response = client.get_health()
    return CommandResults(
        outputs_prefix='CriblAPI.Health',
        outputs_key_field='status',
        outputs=response,
        readable_output=tableToMarkdown('Cribl Health Status', [response], removeNull=True, headerTransform=pascalToSpace),
        raw_response=response,
    )


# --- Master Groups ---

def list_master_groups_command(client: Client, args: dict) -> CommandResults:
    fields = args.get('fields')
    product = args.get('product')
    response = client.list_master_groups(fields, product)
    items = response.get('items', [])
    return CommandResults(
        outputs_prefix='CriblAPI.WorkerGroup',
        outputs_key_field='id',
        outputs=items,
        readable_output=tableToMarkdown('Cribl Worker Groups', items, removeNull=True, headerTransform=pascalToSpace),
        raw_response=response,
    )


def get_master_group_command(client: Client, args: dict) -> CommandResults:
    group_id = args.get('id', '')
    fields = args.get('fields')
    response = client.get_master_group(group_id, fields)
    items = response.get('items', [])
    return CommandResults(
        outputs_prefix='CriblAPI.WorkerGroup',
        outputs_key_field='id',
        outputs=items,
        readable_output=tableToMarkdown(f'Worker Group: {group_id}', items, removeNull=True, headerTransform=pascalToSpace),
        raw_response=response,
    )


def update_master_group_command(client: Client, args: dict) -> CommandResults:
    group_id = args.get('id', '')
    try:
        body = json.loads(args.get('body', '{}'))
    except ValueError as e:
        raise DemistoException(f'Invalid JSON in body argument: {e}')
    response = client.update_master_group(group_id, body)
    items = response.get('items', [])
    return CommandResults(
        outputs_prefix='CriblAPI.WorkerGroup',
        outputs_key_field='id',
        outputs=items,
        readable_output=tableToMarkdown(f'Updated Worker Group: {group_id}', items, removeNull=True, headerTransform=pascalToSpace),
        raw_response=response,
    )


def delete_master_group_command(client: Client, args: dict) -> CommandResults:
    group_id = args.get('id', '')
    response = client.delete_master_group(group_id)
    items = response.get('items', [])
    return CommandResults(
        outputs_prefix='CriblAPI.WorkerGroup',
        outputs_key_field='id',
        outputs=items,
        readable_output=tableToMarkdown(f'Deleted Worker Group: {group_id}', items, removeNull=True, headerTransform=pascalToSpace),
        raw_response=response,
    )


def deploy_master_group_command(client: Client, args: dict) -> CommandResults:
    group_id = args.get('id', '')
    response = client.deploy_master_group(group_id)
    items = response.get('items', [])
    return CommandResults(
        outputs_prefix='CriblAPI.WorkerGroup',
        outputs_key_field='id',
        outputs=items,
        readable_output=tableToMarkdown(f'Deployed Worker Group: {group_id}', items, removeNull=True, headerTransform=pascalToSpace),
        raw_response=response,
    )


def get_master_group_config_version_command(client: Client, args: dict) -> CommandResults:
    group_id = args.get('id', '')
    response = client.get_master_group_config_version(group_id)
    items = response.get('items', [response])
    return CommandResults(
        outputs_prefix='CriblAPI.WorkerGroupConfigVersion',
        outputs=items,
        readable_output=tableToMarkdown(f'Config Version: {group_id}', items, removeNull=True, headerTransform=pascalToSpace),
        raw_response=response,
    )


# --- Product Groups ---

def list_product_groups_command(client: Client, args: dict) -> CommandResults:
    product = args.get('product', 'stream')
    fields = args.get('fields')
    response = client.list_product_groups(product, fields)
    items = response.get('items', [])
    return CommandResults(
        outputs_prefix='CriblAPI.WorkerGroup',
        outputs_key_field='id',
        outputs=items,
        readable_output=tableToMarkdown('Cribl Worker Groups', items, removeNull=True, headerTransform=pascalToSpace),
        raw_response=response,
    )


def get_product_group_command(client: Client, args: dict) -> CommandResults:
    product = args.get('product', 'stream')
    group_id = args.get('id', '')
    fields = args.get('fields')
    response = client.get_product_group(product, group_id, fields)
    items = response.get('items', [])
    return CommandResults(
        outputs_prefix='CriblAPI.WorkerGroup',
        outputs_key_field='id',
        outputs=items,
        readable_output=tableToMarkdown(f'Worker Group: {group_id}', items, removeNull=True, headerTransform=pascalToSpace),
        raw_response=response,
    )


def deploy_product_group_command(client: Client, args: dict) -> CommandResults:
    product = args.get('product', 'stream')
    group_id = args.get('id', '')
    response = client.deploy_product_group(product, group_id)
    items = response.get('items', [])
    return CommandResults(
        outputs_prefix='CriblAPI.WorkerGroup',
        outputs_key_field='id',
        outputs=items,
        readable_output=tableToMarkdown(f'Deployed Worker Group: {group_id}', items, removeNull=True, headerTransform=pascalToSpace),
        raw_response=response,
    )


# --- Workers ---

def list_workers_command(client: Client, args: dict) -> CommandResults:
    product = args.get('product', 'stream')
    limit = arg_to_number(args.get('limit'))
    offset = arg_to_number(args.get('offset'))
    filter_exp = args.get('filter_exp')
    response = client.list_workers(product, limit, offset, filter_exp)
    items = response.get('items', [])
    return CommandResults(
        outputs_prefix='CriblAPI.Worker',
        outputs_key_field='guid',
        outputs=items,
        readable_output=tableToMarkdown('Cribl Workers', items, removeNull=True, headerTransform=pascalToSpace),
        raw_response=response,
    )


def restart_workers_command(client: Client, args: dict) -> CommandResults:
    product = args.get('product', 'stream')
    response = client.restart_workers(product)
    items = response.get('items', [response])
    return CommandResults(
        outputs_prefix='CriblAPI.RestartResponse',
        outputs=items,
        readable_output=tableToMarkdown(f'Restart Workers ({product})', items, removeNull=True, headerTransform=pascalToSpace),
        raw_response=response,
    )


# --- Pipelines ---

def list_pipelines_command(client: Client, args: dict) -> CommandResults:
    worker_group = args.get('worker_group')
    worker_node = args.get('worker_node')
    response = client.list_pipelines(worker_group, worker_node)
    items = response.get('items', [])
    return CommandResults(
        outputs_prefix='CriblAPI.Pipeline',
        outputs_key_field='id',
        outputs=items,
        readable_output=tableToMarkdown('Cribl Pipelines', items, removeNull=True, headerTransform=pascalToSpace),
        raw_response=response,
    )


def get_pipeline_command(client: Client, args: dict) -> CommandResults:
    pipeline_id = args.get('id', '')
    worker_group = args.get('worker_group')
    worker_node = args.get('worker_node')
    response = client.get_pipeline(pipeline_id, worker_group, worker_node)
    items = response.get('items', [])
    return CommandResults(
        outputs_prefix='CriblAPI.Pipeline',
        outputs_key_field='id',
        outputs=items,
        readable_output=tableToMarkdown(f'Pipeline: {pipeline_id}', items, removeNull=True, headerTransform=pascalToSpace),
        raw_response=response,
    )


# --- Sources ---

def list_sources_command(client: Client, args: dict) -> CommandResults:
    source_type = args.get('type')
    worker_group = args.get('worker_group')
    worker_node = args.get('worker_node')
    response = client.list_sources(source_type, worker_group, worker_node)
    items = response.get('items', [])
    return CommandResults(
        outputs_prefix='CriblAPI.Source',
        outputs_key_field='id',
        outputs=items,
        readable_output=tableToMarkdown('Cribl Sources', items, removeNull=True, headerTransform=pascalToSpace),
        raw_response=response,
    )


def get_source_command(client: Client, args: dict) -> CommandResults:
    source_id = args.get('id', '')
    worker_group = args.get('worker_group')
    worker_node = args.get('worker_node')
    response = client.get_source(source_id, worker_group, worker_node)
    items = response.get('items', [])
    return CommandResults(
        outputs_prefix='CriblAPI.Source',
        outputs_key_field='id',
        outputs=items,
        readable_output=tableToMarkdown(f'Source: {source_id}', items, removeNull=True, headerTransform=pascalToSpace),
        raw_response=response,
    )


def list_source_status_command(client: Client, args: dict) -> CommandResults:
    metrics = arg_to_boolean(args.get('metrics')) if args.get('metrics') else None
    limit = arg_to_number(args.get('limit'))
    offset = arg_to_number(args.get('offset'))
    worker_group = args.get('worker_group')
    worker_node = args.get('worker_node')
    response = client.list_source_status(metrics, limit, offset, worker_group, worker_node)
    items = response.get('items', [])
    return CommandResults(
        outputs_prefix='CriblAPI.SourceStatus',
        outputs_key_field='id',
        outputs=items,
        readable_output=tableToMarkdown('Source Status', items, removeNull=True, headerTransform=pascalToSpace),
        raw_response=response,
    )


def get_source_status_command(client: Client, args: dict) -> CommandResults:
    source_id = args.get('id', '')
    metrics = arg_to_boolean(args.get('metrics')) if args.get('metrics') else None
    worker_group = args.get('worker_group')
    worker_node = args.get('worker_node')
    response = client.get_source_status(source_id, metrics, worker_group, worker_node)
    items = response.get('items', [])
    return CommandResults(
        outputs_prefix='CriblAPI.SourceStatus',
        outputs_key_field='id',
        outputs=items,
        readable_output=tableToMarkdown(f'Source Status: {source_id}', items, removeNull=True, headerTransform=pascalToSpace),
        raw_response=response,
    )


# --- Destinations ---

def list_destinations_command(client: Client, args: dict) -> CommandResults:
    dest_type = args.get('type')
    worker_group = args.get('worker_group')
    worker_node = args.get('worker_node')
    response = client.list_destinations(dest_type, worker_group, worker_node)
    items = response.get('items', [])
    return CommandResults(
        outputs_prefix='CriblAPI.Destination',
        outputs_key_field='id',
        outputs=items,
        readable_output=tableToMarkdown('Cribl Destinations', items, removeNull=True, headerTransform=pascalToSpace),
        raw_response=response,
    )


def get_destination_command(client: Client, args: dict) -> CommandResults:
    dest_id = args.get('id', '')
    worker_group = args.get('worker_group')
    worker_node = args.get('worker_node')
    response = client.get_destination(dest_id, worker_group, worker_node)
    items = response.get('items', [])
    return CommandResults(
        outputs_prefix='CriblAPI.Destination',
        outputs_key_field='id',
        outputs=items,
        readable_output=tableToMarkdown(f'Destination: {dest_id}', items, removeNull=True, headerTransform=pascalToSpace),
        raw_response=response,
    )


def list_destination_status_command(client: Client, args: dict) -> CommandResults:
    metrics = arg_to_boolean(args.get('metrics')) if args.get('metrics') else None
    limit = arg_to_number(args.get('limit'))
    offset = arg_to_number(args.get('offset'))
    worker_group = args.get('worker_group')
    worker_node = args.get('worker_node')
    response = client.list_destination_status(metrics, limit, offset, worker_group, worker_node)
    items = response.get('items', [])
    return CommandResults(
        outputs_prefix='CriblAPI.DestinationStatus',
        outputs_key_field='id',
        outputs=items,
        readable_output=tableToMarkdown('Destination Status', items, removeNull=True, headerTransform=pascalToSpace),
        raw_response=response,
    )


def get_destination_status_command(client: Client, args: dict) -> CommandResults:
    dest_id = args.get('id', '')
    metrics = arg_to_boolean(args.get('metrics')) if args.get('metrics') else None
    worker_group = args.get('worker_group')
    worker_node = args.get('worker_node')
    response = client.get_destination_status(dest_id, metrics, worker_group, worker_node)
    items = response.get('items', [])
    return CommandResults(
        outputs_prefix='CriblAPI.DestinationStatus',
        outputs_key_field='id',
        outputs=items,
        readable_output=tableToMarkdown(f'Destination Status: {dest_id}', items, removeNull=True, headerTransform=pascalToSpace),
        raw_response=response,
    )


# --- Jobs ---

def list_jobs_command(client: Client, args: dict) -> CommandResults:
    limit = arg_to_number(args.get('limit'))
    offset = arg_to_number(args.get('offset'))
    run_type = args.get('run_type')
    state = args.get('state')
    collector_id = args.get('collector_id')
    response = client.list_jobs(limit, offset, run_type, state, collector_id)
    items = response.get('items', [])
    return CommandResults(
        outputs_prefix='CriblAPI.Job',
        outputs_key_field='id',
        outputs=items,
        readable_output=tableToMarkdown('Cribl Jobs', items, removeNull=True, headerTransform=pascalToSpace),
        raw_response=response,
    )


def get_job_command(client: Client, args: dict) -> CommandResults:
    job_id = args.get('id', '')
    response = client.get_job(job_id)
    items = response.get('items', [])
    return CommandResults(
        outputs_prefix='CriblAPI.Job',
        outputs_key_field='id',
        outputs=items,
        readable_output=tableToMarkdown(f'Job: {job_id}', items, removeNull=True, headerTransform=pascalToSpace),
        raw_response=response,
    )


def cancel_job_command(client: Client, args: dict) -> CommandResults:
    job_id = args.get('id', '')
    response = client.cancel_job(job_id)
    items = response.get('items', [response])
    return CommandResults(
        outputs_prefix='CriblAPI.JobState',
        outputs=items,
        readable_output=tableToMarkdown(f'Cancelled Job: {job_id}', items, removeNull=True, headerTransform=pascalToSpace),
        raw_response=response,
    )


def pause_job_command(client: Client, args: dict) -> CommandResults:
    job_id = args.get('id', '')
    response = client.pause_job(job_id)
    items = response.get('items', [response])
    return CommandResults(
        outputs_prefix='CriblAPI.JobState',
        outputs=items,
        readable_output=tableToMarkdown(f'Paused Job: {job_id}', items, removeNull=True, headerTransform=pascalToSpace),
        raw_response=response,
    )


def resume_job_command(client: Client, args: dict) -> CommandResults:
    job_id = args.get('id', '')
    response = client.resume_job(job_id)
    items = response.get('items', [response])
    return CommandResults(
        outputs_prefix='CriblAPI.JobState',
        outputs=items,
        readable_output=tableToMarkdown(f'Resumed Job: {job_id}', items, removeNull=True, headerTransform=pascalToSpace),
        raw_response=response,
    )


# --- Lookups ---

def list_lookups_command(client: Client, args: dict) -> CommandResults:
    response = client.list_lookups()
    items = response.get('items', [])
    return CommandResults(
        outputs_prefix='CriblAPI.Lookup',
        outputs_key_field='id',
        outputs=items,
        readable_output=tableToMarkdown('Cribl Lookups', items, removeNull=True, headerTransform=pascalToSpace),
        raw_response=response,
    )


def get_lookup_command(client: Client, args: dict) -> CommandResults:
    lookup_id = args.get('id', '')
    response = client.get_lookup(lookup_id)
    items = response.get('items', [])
    return CommandResults(
        outputs_prefix='CriblAPI.Lookup',
        outputs_key_field='id',
        outputs=items,
        readable_output=tableToMarkdown(f'Lookup: {lookup_id}', items, removeNull=True, headerTransform=pascalToSpace),
        raw_response=response,
    )


# --- Metrics ---

def query_metrics_command(client: Client, args: dict) -> CommandResults:
    filter_expr = args.get('filter_expr')
    pipeline = args.get('pipeline')
    earliest = args.get('earliest')
    latest = args.get('latest')
    num_buckets = arg_to_number(args.get('num_buckets'))
    body = assign_params(
        filterExpr=filter_expr,
        pipeline=pipeline,
        earliest=earliest,
        latest=latest,
        numBuckets=num_buckets,
    )
    response = client.query_metrics(body)
    results = response.get('results', response.get('items', [response]))
    return CommandResults(
        outputs_prefix='CriblAPI.Metrics',
        outputs=results,
        readable_output=tableToMarkdown('Cribl Metrics Query Results', results, removeNull=True, headerTransform=pascalToSpace),
        raw_response=response,
    )


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
            return_results(test_module(auth_client, client_id, client_secret, token_url))
            return

        # Fetch or reuse a cached valid token, then build the real client
        # with the token baked into every request via the Authorization header.
        token = get_valid_token(auth_client, client_id, client_secret, token_url)
        client = Client(
            base_url=base_url,
            api_key=token,
            verify=verify_certificate,
            proxy=proxy,
        )

        commands = {
            'criblapi-get-system-info': get_system_info_command,
            'criblapi-get-health': get_health_command,
            'criblapi-list-master-groups': list_master_groups_command,
            'criblapi-get-master-group': get_master_group_command,
            'criblapi-update-master-group': update_master_group_command,
            'criblapi-delete-master-group': delete_master_group_command,
            'criblapi-deploy-master-group': deploy_master_group_command,
            'criblapi-get-master-group-config-version': get_master_group_config_version_command,
            'criblapi-list-worker-groups': list_product_groups_command,
            'criblapi-get-worker-group': get_product_group_command,
            'criblapi-deploy-worker-group': deploy_product_group_command,
            'criblapi-list-workers': list_workers_command,
            'criblapi-restart-workers': restart_workers_command,
            'criblapi-list-pipelines': list_pipelines_command,
            'criblapi-get-pipeline': get_pipeline_command,
            'criblapi-list-sources': list_sources_command,
            'criblapi-get-source': get_source_command,
            'criblapi-list-source-status': list_source_status_command,
            'criblapi-get-source-status': get_source_status_command,
            'criblapi-list-destinations': list_destinations_command,
            'criblapi-get-destination': get_destination_command,
            'criblapi-list-destination-status': list_destination_status_command,
            'criblapi-get-destination-status': get_destination_status_command,
            'criblapi-list-jobs': list_jobs_command,
            'criblapi-get-job': get_job_command,
            'criblapi-cancel-job': cancel_job_command,
            'criblapi-pause-job': pause_job_command,
            'criblapi-resume-job': resume_job_command,
            'criblapi-list-lookups': list_lookups_command,
            'criblapi-get-lookup': get_lookup_command,
            'criblapi-query-metrics': query_metrics_command,
        }

        if command in commands:
            return_results(commands[command](client, args))
        else:
            raise NotImplementedError(f'Command {command} is not implemented')

    except Exception as e:
        return_error(f'Failed to execute {command} command.\nError:\n{str(e)}')


if __name__ in ('__main__', '__builtin__', 'builtins'):
    main()
