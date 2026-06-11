import json

import urllib3

urllib3.disable_warnings()

""" CONSTANTS """

DEFAULT_PER_PAGE = 50
DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

APP_HEADERS = ["id", "name", "domain_canonical", "category", "account_count", "adoption_percentage", "first_date", "is_ignored"]
ACCOUNT_HEADERS = ["id", "name", "domain_canonical", "app_id", "user_id", "mfa_status", "is_admin", "first_date", "last_date"]
OAUTH_GRANT_HEADERS = ["id", "name", "risk_level", "risk_score", "user_id", "account_id", "oauth_integration", "first_seen", "last_seen"]
EVENT_HEADERS = ["id", "event_id", "type", "date", "user_email", "from_email", "domain_canonical", "account_id"]
USER_HEADERS = ["id", "name", "primary_email", "status", "is_admin", "has_2fa", "creation_time"]
GROUP_HEADERS = ["id", "name", "external_id", "description", "risk_level", "creation_date"]
GROUP_MEMBER_HEADERS = ["id", "member_role", "user"]
NOTIFICATION_HEADERS = ["id", "summary", "status", "creation_date", "target_app_id", "target_account_id", "target_event_id", "target_oauth_grant_id"]
FINDING_HEADERS = ["id", "status", "result", "description", "resource_type_name", "resource_id", "creation_time", "resolution_time"]
FIELD_HEADERS = ["id", "name", "field_type", "scopes", "system_defined", "allowed_values"]
LABEL_HEADERS = ["value", "color", "system_defined"]
INSTANCE_HEADERS = ["id", "name", "display_name", "domain_canonical", "identifier", "connection_status", "sso_label", "first_date"]
APP_INTEGRATION_HEADERS = ["id", "name", "auth_type", "auth_method_name", "risk_level", "risk_score", "status", "app_id", "first_date", "last_date"]
AI_SESSION_HEADERS = ["identifier", "user_id", "saas_id", "service_domain", "start_date", "finish_date", "query_count"]
AI_PROMPT_HEADERS = ["id", "user_id", "prompt_query", "submission_date", "ai_session_identifier"]
BROWSER_EXT_CLIENT_HEADERS = ["id", "guid", "hostname", "browser", "browser_version", "os", "user_id", "registration_status", "last_heartbeat"]
BROWSER_EXT_RECORD_HEADERS = ["id", "status", "version", "deployment_type", "first_date", "last_date", "browser_extension_client_id"]

""" CLIENT CLASS """


class Client(BaseClient):
    def __init__(self, base_url: str, api_token: str, verify: bool, proxy: bool):
        super().__init__(
            base_url=base_url,
            verify=verify,
            proxy=proxy,
            headers={"Authorization": f"Bearer {api_token}", "Content-Type": "application/json"},
        )

    # Apps
    def search_apps(self, body: dict) -> dict:
        return self._http_request("POST", url_suffix="/apps/search", json_data=body)

    def search_apps_supply_chain(self, body: dict) -> dict:
        return self._http_request("POST", url_suffix="/apps/search/supply_chain", json_data=body)

    def get_app(self, app_id: int) -> dict:
        return self._http_request("GET", url_suffix=f"/apps/{app_id}")

    def set_app_category(self, app_id: int, body: dict) -> dict:
        return self._http_request("POST", url_suffix=f"/apps/app-category/{app_id}", json_data=body)

    def set_app_field(self, app_id: int, field_id: int, body: dict) -> dict:
        return self._http_request("POST", url_suffix=f"/apps/{app_id}/fields/{field_id}", json_data=body)

    def delete_app_field(self, app_id: int, field_id: int, body: dict) -> dict:
        return self._http_request("DELETE", url_suffix=f"/apps/{app_id}/fields/{field_id}", json_data=body)

    def add_app_label(self, app_id: int, body: dict) -> dict:
        return self._http_request("POST", url_suffix=f"/apps/{app_id}/labels", json_data=body)

    def delete_app_label(self, app_id: int, body: dict) -> dict:
        return self._http_request("DELETE", url_suffix=f"/apps/{app_id}/labels", json_data=body)

    def search_app_instances(self, app_id: int, body: dict) -> dict:
        return self._http_request("POST", url_suffix=f"/apps/{app_id}/instances/search", json_data=body)

    def set_app_technical_contact(self, app_id: int, user_id: int) -> dict:
        return self._http_request("POST", url_suffix=f"/apps/{app_id}/technical-contact/{user_id}")

    def delete_app_technical_contact(self, app_id: int) -> dict:
        return self._http_request("DELETE", url_suffix=f"/apps/{app_id}/technical-contact")

    # Accounts
    def search_accounts(self, body: dict) -> dict:
        return self._http_request("POST", url_suffix="/accounts/search", json_data=body)

    def get_account(self, account_id: int) -> dict:
        return self._http_request("GET", url_suffix=f"/accounts/{account_id}")

    def set_account_field(self, account_id: int, field_id: int, body: dict) -> dict:
        return self._http_request("POST", url_suffix=f"/accounts/{account_id}/fields/{field_id}", json_data=body)

    def delete_account_field(self, account_id: int, field_id: int, body: dict) -> dict:
        return self._http_request("DELETE", url_suffix=f"/accounts/{account_id}/fields/{field_id}", json_data=body)

    def add_account_label(self, account_id: int, body: dict) -> dict:
        return self._http_request("POST", url_suffix=f"/accounts/{account_id}/labels", json_data=body)

    def delete_account_label(self, account_id: int, body: dict) -> dict:
        return self._http_request("DELETE", url_suffix=f"/accounts/{account_id}/labels", json_data=body)

    # OAuth grants
    def search_oauth_grants(self, body: dict) -> dict:
        return self._http_request("POST", url_suffix="/oauth/grants/search", json_data=body)

    def get_oauth_grant(self, oauth_id: int) -> dict:
        return self._http_request("GET", url_suffix=f"/oauth/grants/{oauth_id}")

    # Events
    def search_events(self, body: dict) -> dict:
        return self._http_request("POST", url_suffix="/events/search", json_data=body)

    def get_event(self, event_id: int) -> dict:
        return self._http_request("GET", url_suffix=f"/events/{event_id}")

    # Users
    def search_users(self, body: dict) -> dict:
        return self._http_request("POST", url_suffix="/users/search", json_data=body)

    def get_user(self, user_id: int) -> dict:
        return self._http_request("GET", url_suffix=f"/users/{user_id}")

    # Groups
    def search_groups(self, body: dict) -> dict:
        return self._http_request("POST", url_suffix="/groups/search", json_data=body)

    def get_group(self, group_id: int) -> dict:
        return self._http_request("GET", url_suffix=f"/groups/{group_id}")

    def search_group_members(self, group_id: int, body: dict) -> dict:
        return self._http_request("POST", url_suffix=f"/groups/{group_id}/members/search", json_data=body)

    # Notifications
    def search_notifications(self, body: dict) -> dict:
        return self._http_request("POST", url_suffix="/notifications/search", json_data=body)

    def get_notification(self, notification_id: int) -> dict:
        return self._http_request("GET", url_suffix=f"/notifications/{notification_id}")

    # Findings
    def search_findings(self, body: dict) -> dict:
        return self._http_request("POST", url_suffix="/findings/search", json_data=body)

    def get_finding(self, finding_id: int) -> dict:
        return self._http_request("GET", url_suffix=f"/findings/{finding_id}")

    # Fields
    def create_field(self, body: dict) -> dict:
        return self._http_request("POST", url_suffix="/fields", json_data=body)

    def search_fields(self, body: dict) -> dict:
        return self._http_request("POST", url_suffix="/fields/search", json_data=body)

    def get_field(self, field_id: int) -> dict:
        return self._http_request("GET", url_suffix=f"/fields/{field_id}")

    def update_field(self, field_id: int, body: dict) -> dict:
        return self._http_request("PUT", url_suffix=f"/fields/{field_id}", json_data=body)

    def delete_field(self, field_id: int) -> dict:
        return self._http_request("DELETE", url_suffix=f"/fields/{field_id}")

    def add_field_allowed_value(self, field_id: int, body: dict) -> dict:
        return self._http_request("POST", url_suffix=f"/fields/{field_id}/allowed_values", json_data=body)

    def update_field_allowed_value(self, field_id: int, body: dict) -> dict:
        return self._http_request("PUT", url_suffix=f"/fields/{field_id}/allowed_values", json_data=body)

    def delete_field_allowed_value(self, field_id: int, body: dict) -> dict:
        return self._http_request("DELETE", url_suffix=f"/fields/{field_id}/allowed_values", json_data=body)

    # Labels
    def create_label(self, body: dict) -> dict:
        return self._http_request("POST", url_suffix="/labels", json_data=body)

    def update_label(self, body: dict) -> dict:
        return self._http_request("PUT", url_suffix="/labels", json_data=body)

    def delete_label(self, body: dict) -> dict:
        return self._http_request("DELETE", url_suffix="/labels", json_data=body)

    def search_labels(self, body: dict) -> dict:
        return self._http_request("POST", url_suffix="/labels/search", json_data=body)

    # App-to-app integrations
    def search_app_integrations(self, body: dict) -> dict:
        return self._http_request("POST", url_suffix="/app_to_app_integrations/other/search", json_data=body)

    def get_app_integration(self, auth_method_id: int) -> dict:
        return self._http_request("GET", url_suffix=f"/app_to_app_integrations/{auth_method_id}")

    # App instances (global)
    def search_instances(self, body: dict) -> dict:
        return self._http_request("POST", url_suffix="/instances/search", json_data=body)

    def get_instance(self, instance_id: int) -> dict:
        return self._http_request("GET", url_suffix=f"/instances/{instance_id}")

    # AI activity
    def search_ai_sessions(self, body: dict) -> dict:
        return self._http_request("POST", url_suffix="/ai-sessions/search", json_data=body)

    def search_ai_prompts(self, body: dict) -> dict:
        return self._http_request("POST", url_suffix="/ai-prompts/search", json_data=body)

    # Browser extension
    def search_browser_extension_clients(self, body: dict) -> dict:
        return self._http_request("POST", url_suffix="/browser-extension/clients/search", json_data=body)

    def search_browser_extension_records(self, body: dict) -> dict:
        return self._http_request("POST", url_suffix="/browser-extension/records/search", json_data=body)

    # Playbooks
    def start_offboarding(self, body: dict) -> dict:
        return self._http_request("POST", url_suffix="/playbooks/offboarding", json_data=body)


""" HELPER FUNCTIONS """


def parse_conditions(value: str | None, arg_name: str) -> list | None:
    """Parses a filters/search argument from a JSON string into a list of condition objects."""
    if not value:
        return None
    try:
        conditions = json.loads(value)
    except json.JSONDecodeError as e:
        raise DemistoException(
            f'Failed to parse the "{arg_name}" argument as JSON: {e}. '
            'Expected format: [{"property": "name", "op": "ilike", "value": "%slack%"}]'
        )
    if isinstance(conditions, dict):
        conditions = [conditions]
    if not isinstance(conditions, list):
        raise DemistoException(f'The "{arg_name}" argument must be a JSON object or a list of JSON objects.')
    return conditions


def build_search_body(args: dict) -> dict:
    """Builds the common request body shared by all Nudge Security search endpoints."""
    sorting = None
    if sort_by := args.get("sort_by"):
        sorting = {"property": sort_by, "direction": args.get("sort_direction") or "asc"}
    return assign_params(
        filters=parse_conditions(args.get("filters"), "filters"),
        search=parse_conditions(args.get("search"), "search"),
        page=arg_to_number(args.get("page"), arg_name="page"),
        per_page=arg_to_number(args.get("per_page"), arg_name="per_page") or DEFAULT_PER_PAGE,
        sorting=sorting,
    )


def build_date_filters(property_name: str, args: dict) -> list:
    """Builds range filter conditions on a date property from start_date/end_date arguments."""
    conditions = []
    if start_date := arg_to_datetime(args.get("start_date"), arg_name="start_date"):
        conditions.append({"property": property_name, "op": ">=", "value": start_date.strftime(DATE_FORMAT)})
    if end_date := arg_to_datetime(args.get("end_date"), arg_name="end_date"):
        conditions.append({"property": property_name, "op": "<=", "value": end_date.strftime(DATE_FORMAT)})
    return conditions


def page_search_results(
    response: dict, title: str, outputs_prefix: str, key_field: str = "id", headers: list | None = None
) -> CommandResults:
    """Builds CommandResults from a paginated Nudge Security search response."""
    values = response.get("values") or []
    table_title = (
        f"{title} (page {response.get('page')} of {response.get('total_pages')}, {response.get('total_values')} total)"
    )
    return CommandResults(
        outputs_prefix=outputs_prefix,
        outputs_key_field=key_field,
        outputs=values,
        readable_output=tableToMarkdown(
            table_title, values, headers=headers, headerTransform=string_to_table_header, removeNull=True
        ),
        raw_response=response,
    )


def single_entity_results(response: dict, title: str, outputs_prefix: str, key_field: str = "id") -> CommandResults:
    """Builds CommandResults for a single entity returned by a get endpoint."""
    return CommandResults(
        outputs_prefix=outputs_prefix,
        outputs_key_field=key_field,
        outputs=response,
        readable_output=tableToMarkdown(title, response, headerTransform=string_to_table_header, removeNull=True),
        raw_response=response,
    )


""" COMMAND FUNCTIONS """


def test_module(client: Client) -> str:
    try:
        client.search_users({"per_page": 1})
    except DemistoException as e:
        if "401" in str(e) or "Unauthorized" in str(e) or "Forbidden" in str(e):
            return "Authorization Error: make sure the API Token is correctly set"
        raise
    return "ok"


# Apps


def app_search_command(client: Client, args: dict) -> CommandResults:
    response = client.search_apps(build_search_body(args))
    return page_search_results(response, "Apps", "Nudge.App", headers=APP_HEADERS)


def app_supply_chain_search_command(client: Client, args: dict) -> CommandResults:
    body = build_search_body(args)
    body["category"] = args.get("category")
    response = client.search_apps_supply_chain(body)
    return page_search_results(response, f'Supply Chain Apps - {args.get("category")}', "Nudge.App", headers=APP_HEADERS)


def app_get_command(client: Client, args: dict) -> CommandResults:
    app_id = arg_to_number(args.get("app_id"), arg_name="app_id", required=True)
    response = client.get_app(app_id)
    return single_entity_results(response, f"App {app_id}", "Nudge.App")


def app_category_set_command(client: Client, args: dict) -> CommandResults:
    app_id = arg_to_number(args.get("app_id"), arg_name="app_id", required=True)
    category = args.get("category")
    response = client.set_app_category(app_id, {"category": category})
    return CommandResults(
        readable_output=f'Category of app {app_id} was set to "{category}".',
        raw_response=response,
    )


def app_field_set_command(client: Client, args: dict) -> CommandResults:
    app_id = arg_to_number(args.get("app_id"), arg_name="app_id", required=True)
    field_id = arg_to_number(args.get("field_id"), arg_name="field_id", required=True)
    value = args.get("value")
    response = client.set_app_field(app_id, field_id, {"value": value})
    return CommandResults(
        outputs_prefix="Nudge.AppField",
        outputs_key_field="id",
        outputs=response,
        readable_output=f'Field {field_id} on app {app_id} was set to "{value}".',
        raw_response=response,
    )


def app_field_delete_command(client: Client, args: dict) -> CommandResults:
    app_id = arg_to_number(args.get("app_id"), arg_name="app_id", required=True)
    field_id = arg_to_number(args.get("field_id"), arg_name="field_id", required=True)
    response = client.delete_app_field(app_id, field_id, assign_params(value=args.get("value")))
    return CommandResults(
        readable_output=f"Field {field_id} was deleted from app {app_id}.",
        raw_response=response,
    )


def app_label_add_command(client: Client, args: dict) -> CommandResults:
    app_id = arg_to_number(args.get("app_id"), arg_name="app_id", required=True)
    value = args.get("value")
    response = client.add_app_label(app_id, {"value": value})
    return CommandResults(
        readable_output=f'Label "{value}" was added to app {app_id}.',
        raw_response=response,
    )


def app_label_delete_command(client: Client, args: dict) -> CommandResults:
    app_id = arg_to_number(args.get("app_id"), arg_name="app_id", required=True)
    value = args.get("value")
    response = client.delete_app_label(app_id, {"value": value})
    return CommandResults(
        readable_output=f'Label "{value}" was deleted from app {app_id}.',
        raw_response=response,
    )


def app_instance_search_command(client: Client, args: dict) -> CommandResults:
    app_id = arg_to_number(args.get("app_id"), arg_name="app_id", required=True)
    response = client.search_app_instances(app_id, build_search_body(args))
    return page_search_results(response, f"Instances of App {app_id}", "Nudge.AppInstance", headers=INSTANCE_HEADERS)


def app_technical_contact_set_command(client: Client, args: dict) -> CommandResults:
    app_id = arg_to_number(args.get("app_id"), arg_name="app_id", required=True)
    user_id = arg_to_number(args.get("user_id"), arg_name="user_id", required=True)
    response = client.set_app_technical_contact(app_id, user_id)
    return CommandResults(
        readable_output=f"User {user_id} was set as the technical contact of app {app_id}.",
        raw_response=response,
    )


def app_technical_contact_delete_command(client: Client, args: dict) -> CommandResults:
    app_id = arg_to_number(args.get("app_id"), arg_name="app_id", required=True)
    response = client.delete_app_technical_contact(app_id)
    return CommandResults(
        readable_output=f"The technical contact of app {app_id} was removed.",
        raw_response=response,
    )


# Accounts


def account_search_command(client: Client, args: dict) -> CommandResults:
    response = client.search_accounts(build_search_body(args))
    return page_search_results(response, "Accounts", "Nudge.Account", headers=ACCOUNT_HEADERS)


def account_get_command(client: Client, args: dict) -> CommandResults:
    account_id = arg_to_number(args.get("account_id"), arg_name="account_id", required=True)
    response = client.get_account(account_id)
    return single_entity_results(response, f"Account {account_id}", "Nudge.Account")


def account_field_set_command(client: Client, args: dict) -> CommandResults:
    account_id = arg_to_number(args.get("account_id"), arg_name="account_id", required=True)
    field_id = arg_to_number(args.get("field_id"), arg_name="field_id", required=True)
    value = args.get("value")
    response = client.set_account_field(account_id, field_id, {"value": value})
    return CommandResults(
        outputs_prefix="Nudge.AccountField",
        outputs_key_field="id",
        outputs=response,
        readable_output=f'Field {field_id} on account {account_id} was set to "{value}".',
        raw_response=response,
    )


def account_field_delete_command(client: Client, args: dict) -> CommandResults:
    account_id = arg_to_number(args.get("account_id"), arg_name="account_id", required=True)
    field_id = arg_to_number(args.get("field_id"), arg_name="field_id", required=True)
    response = client.delete_account_field(account_id, field_id, assign_params(value=args.get("value")))
    return CommandResults(
        readable_output=f"Field {field_id} was deleted from account {account_id}.",
        raw_response=response,
    )


def account_label_add_command(client: Client, args: dict) -> CommandResults:
    account_id = arg_to_number(args.get("account_id"), arg_name="account_id", required=True)
    value = args.get("value")
    response = client.add_account_label(account_id, {"value": value})
    return CommandResults(
        readable_output=f'Label "{value}" was added to account {account_id}.',
        raw_response=response,
    )


def account_label_delete_command(client: Client, args: dict) -> CommandResults:
    account_id = arg_to_number(args.get("account_id"), arg_name="account_id", required=True)
    value = args.get("value")
    response = client.delete_account_label(account_id, {"value": value})
    return CommandResults(
        readable_output=f'Label "{value}" was deleted from account {account_id}.',
        raw_response=response,
    )


# OAuth grants


def oauth_grant_search_command(client: Client, args: dict) -> CommandResults:
    response = client.search_oauth_grants(build_search_body(args))
    return page_search_results(response, "OAuth Grants", "Nudge.OAuthGrant", headers=OAUTH_GRANT_HEADERS)


def oauth_grant_get_command(client: Client, args: dict) -> CommandResults:
    oauth_id = arg_to_number(args.get("oauth_id"), arg_name="oauth_id", required=True)
    response = client.get_oauth_grant(oauth_id)
    return single_entity_results(response, f"OAuth Grant {oauth_id}", "Nudge.OAuthGrant")


# Events


def event_search_command(client: Client, args: dict) -> CommandResults:
    body = build_search_body(args)
    if date_filters := build_date_filters("date", args):
        body["filters"] = (body.get("filters") or []) + date_filters
    response = client.search_events(body)
    return page_search_results(response, "Events", "Nudge.Event", headers=EVENT_HEADERS)


def event_get_command(client: Client, args: dict) -> CommandResults:
    event_id = arg_to_number(args.get("event_id"), arg_name="event_id", required=True)
    response = client.get_event(event_id)
    return single_entity_results(response, f"Event {event_id}", "Nudge.Event")


# Users


def user_search_command(client: Client, args: dict) -> CommandResults:
    response = client.search_users(build_search_body(args))
    return page_search_results(response, "Users", "Nudge.User", headers=USER_HEADERS)


def user_get_command(client: Client, args: dict) -> CommandResults:
    user_id = arg_to_number(args.get("user_id"), arg_name="user_id", required=True)
    response = client.get_user(user_id)
    return single_entity_results(response, f"User {user_id}", "Nudge.User")


# Groups


def group_search_command(client: Client, args: dict) -> CommandResults:
    response = client.search_groups(build_search_body(args))
    return page_search_results(response, "Groups", "Nudge.Group", headers=GROUP_HEADERS)


def group_get_command(client: Client, args: dict) -> CommandResults:
    group_id = arg_to_number(args.get("group_id"), arg_name="group_id", required=True)
    response = client.get_group(group_id)
    return single_entity_results(response, f"Group {group_id}", "Nudge.Group")


def group_member_search_command(client: Client, args: dict) -> CommandResults:
    group_id = arg_to_number(args.get("group_id"), arg_name="group_id", required=True)
    response = client.search_group_members(group_id, build_search_body(args))
    return page_search_results(response, f"Members of Group {group_id}", "Nudge.GroupMember", headers=GROUP_MEMBER_HEADERS)


# Notifications


def notification_search_command(client: Client, args: dict) -> CommandResults:
    response = client.search_notifications(build_search_body(args))
    return page_search_results(response, "Notifications", "Nudge.Notification", headers=NOTIFICATION_HEADERS)


def notification_get_command(client: Client, args: dict) -> CommandResults:
    notification_id = arg_to_number(args.get("notification_id"), arg_name="notification_id", required=True)
    response = client.get_notification(notification_id)
    return single_entity_results(response, f"Notification {notification_id}", "Nudge.Notification")


# Findings


def finding_search_command(client: Client, args: dict) -> CommandResults:
    response = client.search_findings(build_search_body(args))
    return page_search_results(response, "Findings", "Nudge.Finding", headers=FINDING_HEADERS)


def finding_get_command(client: Client, args: dict) -> CommandResults:
    finding_id = arg_to_number(args.get("finding_id"), arg_name="finding_id", required=True)
    response = client.get_finding(finding_id)
    return single_entity_results(response, f"Finding {finding_id}", "Nudge.Finding")


# Fields


def field_create_command(client: Client, args: dict) -> CommandResults:
    body = {
        "name": args.get("name"),
        "field_type": args.get("field_type"),
        "scopes": argToList(args.get("scopes")),
    }
    response = client.create_field(body)
    field = response.get("field") or {}
    return CommandResults(
        outputs_prefix="Nudge.Field",
        outputs_key_field="id",
        outputs=field,
        readable_output=tableToMarkdown(
            "Field Created", field, headers=FIELD_HEADERS, headerTransform=string_to_table_header, removeNull=True
        ),
        raw_response=response,
    )


def field_search_command(client: Client, args: dict) -> CommandResults:
    response = client.search_fields(build_search_body(args))
    return page_search_results(response, "Fields", "Nudge.Field", headers=FIELD_HEADERS)


def field_get_command(client: Client, args: dict) -> CommandResults:
    field_id = arg_to_number(args.get("field_id"), arg_name="field_id", required=True)
    response = client.get_field(field_id)
    return single_entity_results(response, f"Field {field_id}", "Nudge.Field")


def field_update_command(client: Client, args: dict) -> CommandResults:
    field_id = arg_to_number(args.get("field_id"), arg_name="field_id", required=True)
    body = assign_params(
        name=args.get("name"),
        scopes=argToList(args.get("scopes")) or None,
    )
    response = client.update_field(field_id, body)
    field = response.get("field") or {}
    return CommandResults(
        outputs_prefix="Nudge.Field",
        outputs_key_field="id",
        outputs=field,
        readable_output=f"Field {field_id} was updated.",
        raw_response=response,
    )


def field_delete_command(client: Client, args: dict) -> CommandResults:
    field_id = arg_to_number(args.get("field_id"), arg_name="field_id", required=True)
    response = client.delete_field(field_id)
    return CommandResults(
        readable_output=f"Field {field_id} was deleted.",
        raw_response=response,
    )


def field_allowed_value_add_command(client: Client, args: dict) -> CommandResults:
    field_id = arg_to_number(args.get("field_id"), arg_name="field_id", required=True)
    body = assign_params(
        value=args.get("value"),
        color=args.get("color"),
        background_color=args.get("background_color"),
        text_color=args.get("text_color"),
    )
    response = client.add_field_allowed_value(field_id, body)
    return CommandResults(
        outputs_prefix="Nudge.FieldAllowedValue",
        outputs_key_field="value",
        outputs=response.get("allowed_value"),
        readable_output=f'Allowed value "{args.get("value")}" was added to field {field_id}.',
        raw_response=response,
    )


def field_allowed_value_update_command(client: Client, args: dict) -> CommandResults:
    field_id = arg_to_number(args.get("field_id"), arg_name="field_id", required=True)
    body = assign_params(
        value=args.get("value"),
        new_value=args.get("new_value"),
        color=args.get("color"),
        background_color=args.get("background_color"),
        text_color=args.get("text_color"),
    )
    response = client.update_field_allowed_value(field_id, body)
    return CommandResults(
        outputs_prefix="Nudge.FieldAllowedValue",
        outputs_key_field="value",
        outputs=response.get("allowed_value"),
        readable_output=f'Allowed value "{args.get("value")}" of field {field_id} was updated.',
        raw_response=response,
    )


def field_allowed_value_delete_command(client: Client, args: dict) -> CommandResults:
    field_id = arg_to_number(args.get("field_id"), arg_name="field_id", required=True)
    value = args.get("value")
    response = client.delete_field_allowed_value(field_id, {"value": value})
    return CommandResults(
        readable_output=f'Allowed value "{value}" was deleted from field {field_id}.',
        raw_response=response,
    )


# Labels


def label_create_command(client: Client, args: dict) -> CommandResults:
    body = assign_params(
        value=args.get("value"),
        color=args.get("color"),
        background_color=args.get("background_color"),
        text_color=args.get("text_color"),
    )
    response = client.create_label(body)
    return CommandResults(
        outputs_prefix="Nudge.Label",
        outputs_key_field="value",
        outputs=response.get("label"),
        readable_output=f'Label "{args.get("value")}" was created.',
        raw_response=response,
    )


def label_update_command(client: Client, args: dict) -> CommandResults:
    body = assign_params(
        value=args.get("value"),
        new_value=args.get("new_value"),
        color=args.get("color"),
        background_color=args.get("background_color"),
        text_color=args.get("text_color"),
    )
    response = client.update_label(body)
    return CommandResults(
        outputs_prefix="Nudge.Label",
        outputs_key_field="value",
        outputs=response.get("label"),
        readable_output=f'Label "{args.get("value")}" was updated.',
        raw_response=response,
    )


def label_delete_command(client: Client, args: dict) -> CommandResults:
    value = args.get("value")
    response = client.delete_label({"value": value})
    return CommandResults(
        readable_output=f'Label "{value}" was deleted.',
        raw_response=response,
    )


def label_search_command(client: Client, args: dict) -> CommandResults:
    response = client.search_labels(build_search_body(args))
    return page_search_results(response, "Labels", "Nudge.Label", key_field="value", headers=LABEL_HEADERS)


# App-to-app integrations


def app_integration_search_command(client: Client, args: dict) -> CommandResults:
    response = client.search_app_integrations(build_search_body(args))
    return page_search_results(response, "App-to-App Integrations", "Nudge.AppIntegration", headers=APP_INTEGRATION_HEADERS)


def app_integration_get_command(client: Client, args: dict) -> CommandResults:
    auth_method_id = arg_to_number(args.get("auth_method_id"), arg_name="auth_method_id", required=True)
    response = client.get_app_integration(auth_method_id)
    return single_entity_results(response, f"App-to-App Integration {auth_method_id}", "Nudge.AppIntegration")


# App instances (global)


def instance_search_command(client: Client, args: dict) -> CommandResults:
    response = client.search_instances(build_search_body(args))
    return page_search_results(response, "App Instances", "Nudge.AppInstance", headers=INSTANCE_HEADERS)


def instance_get_command(client: Client, args: dict) -> CommandResults:
    instance_id = arg_to_number(args.get("instance_id"), arg_name="instance_id", required=True)
    response = client.get_instance(instance_id)
    return single_entity_results(response, f"App Instance {instance_id}", "Nudge.AppInstance")


# AI activity


def ai_session_search_command(client: Client, args: dict) -> CommandResults:
    body = build_search_body(args)
    body["filters"] = (body.get("filters") or []) + build_date_filters("start_date", args)
    response = client.search_ai_sessions(body)
    return page_search_results(response, "AI Sessions", "Nudge.AiSession", key_field="identifier", headers=AI_SESSION_HEADERS)


def ai_prompt_search_command(client: Client, args: dict) -> CommandResults:
    body = build_search_body(args)
    body["filters"] = (body.get("filters") or []) + build_date_filters("submission_date", args)
    response = client.search_ai_prompts(body)
    return page_search_results(response, "AI Prompts", "Nudge.AiPrompt", headers=AI_PROMPT_HEADERS)


# Browser extension


def browser_extension_client_search_command(client: Client, args: dict) -> CommandResults:
    response = client.search_browser_extension_clients(build_search_body(args))
    return page_search_results(
        response, "Browser Extension Clients", "Nudge.BrowserExtensionClient", headers=BROWSER_EXT_CLIENT_HEADERS
    )


def browser_extension_record_search_command(client: Client, args: dict) -> CommandResults:
    response = client.search_browser_extension_records(build_search_body(args))
    return page_search_results(
        response, "Browser Extension Records", "Nudge.BrowserExtensionRecord", headers=BROWSER_EXT_RECORD_HEADERS
    )


# Playbooks


def offboarding_start_command(client: Client, args: dict) -> CommandResults:
    user_id = arg_to_number(args.get("user_id"), arg_name="user_id", required=True)
    response = client.start_offboarding({"user_id": user_id})
    outputs = {"user_id": user_id, "url": response.get("url")}
    return CommandResults(
        outputs_prefix="Nudge.Offboarding",
        outputs_key_field="user_id",
        outputs=outputs,
        readable_output=f'Offboarding was started for user {user_id}. Track progress at: {response.get("url")}',
        raw_response=response,
    )


""" MAIN FUNCTION """


def main() -> None:
    params = demisto.params()
    args = demisto.args()
    command = demisto.command()

    base_url = params.get("url", "").rstrip("/") + "/api/1.0"
    api_token = params.get("apikey") or (params.get("credentials") or {}).get("password", "")
    verify_certificate = not params.get("insecure", False)
    proxy = params.get("proxy", False)

    demisto.debug(f"Command being called is {command}")

    try:
        if not api_token:
            raise DemistoException("API Token is required. Please set it in the instance configuration.")

        client = Client(
            base_url=base_url,
            api_token=api_token,
            verify=verify_certificate,
            proxy=proxy,
        )

        commands = {
            "nudge-app-search": app_search_command,
            "nudge-app-supply-chain-search": app_supply_chain_search_command,
            "nudge-app-get": app_get_command,
            "nudge-app-category-set": app_category_set_command,
            "nudge-app-field-set": app_field_set_command,
            "nudge-app-field-delete": app_field_delete_command,
            "nudge-app-label-add": app_label_add_command,
            "nudge-app-label-delete": app_label_delete_command,
            "nudge-app-instance-search": app_instance_search_command,
            "nudge-app-technical-contact-set": app_technical_contact_set_command,
            "nudge-app-technical-contact-delete": app_technical_contact_delete_command,
            "nudge-account-search": account_search_command,
            "nudge-account-get": account_get_command,
            "nudge-account-field-set": account_field_set_command,
            "nudge-account-field-delete": account_field_delete_command,
            "nudge-account-label-add": account_label_add_command,
            "nudge-account-label-delete": account_label_delete_command,
            "nudge-oauth-grant-search": oauth_grant_search_command,
            "nudge-oauth-grant-get": oauth_grant_get_command,
            "nudge-event-search": event_search_command,
            "nudge-event-get": event_get_command,
            "nudge-user-search": user_search_command,
            "nudge-user-get": user_get_command,
            "nudge-group-search": group_search_command,
            "nudge-group-get": group_get_command,
            "nudge-group-member-search": group_member_search_command,
            "nudge-notification-search": notification_search_command,
            "nudge-notification-get": notification_get_command,
            "nudge-finding-search": finding_search_command,
            "nudge-finding-get": finding_get_command,
            "nudge-field-create": field_create_command,
            "nudge-field-search": field_search_command,
            "nudge-field-get": field_get_command,
            "nudge-field-update": field_update_command,
            "nudge-field-delete": field_delete_command,
            "nudge-field-allowed-value-add": field_allowed_value_add_command,
            "nudge-field-allowed-value-update": field_allowed_value_update_command,
            "nudge-field-allowed-value-delete": field_allowed_value_delete_command,
            "nudge-label-create": label_create_command,
            "nudge-label-update": label_update_command,
            "nudge-label-delete": label_delete_command,
            "nudge-label-search": label_search_command,
            "nudge-app-integration-search": app_integration_search_command,
            "nudge-app-integration-get": app_integration_get_command,
            "nudge-instance-search": instance_search_command,
            "nudge-instance-get": instance_get_command,
            "nudge-ai-session-search": ai_session_search_command,
            "nudge-ai-prompt-search": ai_prompt_search_command,
            "nudge-browser-extension-client-search": browser_extension_client_search_command,
            "nudge-browser-extension-record-search": browser_extension_record_search_command,
            "nudge-offboarding-start": offboarding_start_command,
        }

        if command == "test-module":
            return_results(test_module(client))
        elif command in commands:
            return_results(commands[command](client, args))
        else:
            raise NotImplementedError(f"Command {command} is not implemented")

    except Exception as e:
        return_error(f"Failed to execute {command} command.\nError:\n{str(e)}")


""" ENTRY POINT """


if __name__ in ("__main__", "__builtin__", "builtins"):
    main()
