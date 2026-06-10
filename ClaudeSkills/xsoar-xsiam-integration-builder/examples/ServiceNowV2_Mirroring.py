# Mirroring Reference — extracted from ServiceNowv2 (Packs/ServiceNow/Integrations/ServiceNowv2)
#
# Mirroring keeps an XSOAR incident and a remote ticket in sync in real time.
# Three commands power it:
#   get-remote-data           — XSOAR pulls updates FROM the remote system into an incident
#   update-remote-system      — XSOAR pushes local changes (fields + entries) TO the remote system
#   get-modified-remote-data  — XSOAR polls to find which remote IDs changed since last check
#
# Additionally, each fetched incident must carry mirror metadata so XSOAR knows how to route it.

import demistomock as demisto
from CommonServerPython import *

# ── 1. Mirror direction constant ──────────────────────────────────────────────
# Maps the user-facing dropdown value to the XSOAR internal direction string.

MIRROR_DIRECTION = {
    "None": None,
    "Incoming": "In",
    "Outgoing": "Out",
    "Incoming And Outgoing": "Both",
}


# ── 2. Mirror metadata attached to every fetched incident ────────────────────
# Call get_mirroring() when building incident dicts in fetch_incidents and merge
# its return value into the incident dict.  XSOAR reads these fields to decide
# which integration instance owns the mirror and which entry tags trigger pushes.

def get_mirroring():
    params = demisto.params()
    return {
        "mirror_direction": MIRROR_DIRECTION.get(params.get("mirror_direction")),
        "mirror_tags": [
            params.get("comment_tag"),                # tag that sends an entry as a comment → remote
            params.get("comment_tag_from_servicenow"),# tag that marks a comment received ← remote
            params.get("file_tag"),                   # tag that sends a file → remote
            params.get("file_tag_from_service_now"),  # tag that marks a file received ← remote
            params.get("work_notes_tag"),             # tag that sends a work note → remote
            params.get("work_notes_tag_from_servicenow"),
        ],
        "mirror_instance": demisto.integrationInstance(),
    }


# Usage in fetch_incidents:
#
#   incident = {
#       "name": f"ServiceNow Incident {ticket_id}",
#       "occurred": ticket.get("sys_created_on"),
#       "rawJSON": json.dumps(ticket),
#       "severity": ...,
#   }
#   incident.update(get_mirroring())   # <-- attach mirror metadata
#   incidents.append(incident)


# ── 3. store_ids_for_first_mirroring ─────────────────────────────────────────
# Optional but recommended: store newly fetched IDs so get-modified-remote-data
# can immediately trigger a mirror-in for brand-new incidents, ensuring any
# existing comments/files on the remote ticket are pulled in right away.

def store_ids_for_first_mirroring(incidents: list):
    int_context = get_integration_context()
    int_context.setdefault("last_fetched_incident_ids", []).extend(
        [incident["sys_id"] for incident in incidents]
    )
    set_integration_context(int_context)


# ── 4. get-remote-data command ───────────────────────────────────────────────
# XSOAR calls this to pull updates for a specific incident.
# Returns: [updated_incident_fields_dict] + [list of new entry dicts]
# The first element updates incident fields; subsequent elements become War Room entries.

def get_remote_data_command(client, args: dict, params: dict):
    ticket_id = args.get("id", "")
    last_update = arg_to_timestamp(arg=args.get("lastUpdate"), arg_name="lastUpdate", required=True)

    result = client.get_ticket(ticket_id)
    if not result:
        return f"Ticket {ticket_id} was not found."

    ticket = result  # dict of field->value

    ticket_last_update = arg_to_timestamp(arg=ticket.get("sys_updated_on"), arg_name="sys_updated_on", required=False)

    # Skip if nothing changed since last pull
    if last_update > ticket_last_update:
        ticket = {}

    entries = []

    # Pull new attachments from remote → tag them so they don't get re-mirrored back
    file_entries = client.get_ticket_attachments(ticket_id, since=datetime.fromtimestamp(last_update))
    for file_entry in file_entries:
        if "_mirrored_from_xsoar" not in file_entry.get("File", ""):
            file_entry["Tags"] = [params.get("file_tag_from_service_now")]
            entries.append(file_entry)

    # Pull new comments/work notes from remote
    comments = client.get_comments(ticket_id, since=datetime.fromtimestamp(last_update))
    for comment in comments:
        tag = (
            params.get("work_notes_tag_from_servicenow")
            if comment.get("element") == "work_notes"
            else params.get("comment_tag_from_servicenow")
        )
        entries.append({
            "Type": EntryType.NOTE,
            "Contents": f"**{comment.get('sys_created_by')}**: {comment.get('value')}",
            "ContentsFormat": EntryFormat.MARKDOWN,
            "Tags": [tag],
        })

    # Close the XSOAR incident if the remote ticket is closed/resolved
    close_incident = params.get("close_incident")
    if close_incident != "None":
        if (
            (ticket.get("closed_at") and close_incident == "closed")
            or (ticket.get("resolved_at") and close_incident == "resolved")
        ):
            entries.append({
                "Type": EntryType.NOTE,
                "Contents": {
                    "dbotIncidentClose": True,
                    "closeNotes": ticket.get("close_notes", ""),
                    "closeReason": "Resolved",
                },
                "ContentsFormat": EntryFormat.JSON,
            })

    return [ticket] + entries


# ── 5. update-remote-system command ─────────────────────────────────────────
# XSOAR calls this when the local incident changes. Push the delta to the remote.
# Must return the remote incident ID (string).

def update_remote_system_command(client, args: dict, params: dict) -> str:
    parsed_args = UpdateRemoteSystemArgs(args)
    ticket_id = parsed_args.remote_incident_id

    # Push changed fields if the incident actually changed
    if parsed_args.incident_changed:
        delta = parsed_args.delta or {}
        if delta:
            # Handle closure: map XSOAR close → remote ticket state
            if parsed_args.inc_status == IncidentStatus.DONE:
                delta["state"] = "6"        # ServiceNow "Resolved" state code
                delta.setdefault("close_notes", parsed_args.data.get("closeReason", "Closed in XSOAR"))
            client.update_ticket(ticket_id, fields=delta)

    # Push new entries (comments, work notes, files) tagged for outbound mirroring
    for entry in parsed_args.entries or []:
        entry_type = entry.get("type")
        tags = entry.get("tags", [])

        # File entries
        if entry_type in (EntryType.FILE, EntryType.IMAGE):
            if params.get("file_tag_from_service_now") not in tags:  # don't re-mirror inbound files
                try:
                    path = demisto.getFilePath(entry.get("id"))
                    file_name = os.path.basename(path.get("name", ""))
                    name_no_ext, ext = os.path.splitext(file_name)
                    client.upload_file(ticket_id, entry.get("id"), name_no_ext + "_mirrored_from_xsoar" + ext)
                except Exception as e:
                    client.add_comment(ticket_id, "comments",
                                       f"File mirror failed: {file_name}\nError: {e}")
        else:
            # Comment / work note text entries
            key = ""
            if params.get("work_notes_tag") in tags:
                key = "work_notes"
            elif params.get("comment_tag") in tags:
                key = "comments"
            if key:
                user = entry.get("user") or "dbot"
                text = f"({user}): {entry.get('contents', '')}\n\nMirrored from Cortex XSOAR"
                client.add_comment(ticket_id, key, text)

    return ticket_id


# ── 6. get-modified-remote-data command ─────────────────────────────────────
# XSOAR polls this on a schedule to discover which remote IDs changed.
# Returns GetModifiedRemoteDataResponse with a list of remote IDs to re-pull.

def get_modified_remote_data_command(client, args: dict, mirror_limit: str = "100") -> GetModifiedRemoteDataResponse:
    remote_args = GetModifiedRemoteDataArgs(args)
    last_update = dateparser.parse(remote_args.last_update, settings={"TIMEZONE": "UTC"})
    if last_update is None:
        last_update = datetime(1970, 1, 1, tzinfo=UTC)
    last_update_str = last_update.strftime("%Y-%m-%d %H:%M:%S")

    result = client.query_tickets(
        query=f"sys_updated_on>{last_update_str}",
        limit=mirror_limit,
        fields="sys_id",
    )

    modified_ids = [r.get("sys_id") for r in result if r.get("sys_id")]

    # Also include brand-new incident IDs stored by store_ids_for_first_mirroring()
    int_context = get_integration_context()
    new_ids = int_context.pop("last_fetched_incident_ids", [])
    if new_ids:
        set_integration_context(int_context)
    modified_ids = list(set(modified_ids + new_ids))

    return GetModifiedRemoteDataResponse(modified_ids)


# ── 7. main() wiring ─────────────────────────────────────────────────────────
# Mirror commands must be registered in main() alongside regular commands.

def main() -> None:
    params = demisto.params()
    args = demisto.args()
    command = demisto.command()

    client = None  # instantiate your Client here

    try:
        if command == "test-module":
            return_results("ok")

        elif command == "fetch-incidents":
            # ... fetch logic ...
            pass

        # ── Mirroring commands ──
        elif command == "get-remote-data":
            return_results(get_remote_data_command(client, args, params))

        elif command == "update-remote-system":
            return_results(update_remote_system_command(client, args, params))

        elif command == "get-modified-remote-data":
            return_results(get_modified_remote_data_command(client, args,
                           mirror_limit=params.get("mirror_limit", "100")))

        else:
            raise NotImplementedError(f"Command {command} is not implemented")

    except Exception as e:
        return_error(f"Failed to execute {command} command.\nError:\n{str(e)}")


if __name__ in ("__main__", "__builtin__", "builtins"):
    main()
