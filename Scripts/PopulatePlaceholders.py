import re
import json

def get_label(incident: dict, path: str):
    """
    Helper: Get specific label from incident/issue labels.
    """
    parts = path.split('.')
    if len(parts) < 3:
        return None

    label = parts[2]
    labels = incident.get('labels', [])

    if not labels:
        return None

    for l in labels:
        if l.get('type') == label:
            return l.get('value')

    return None

def flatten_to_lowercase_keys(obj, prefix='', result_map=None):
    """
    Helper: Recursively flattens a dictionary and its nested structures,
    casting all keys to lowercase to allow for case-insensitive matching.
    It maps both the base key (e.g., "region") and the dotted path (e.g., "sqlresults.region").
    """
    if result_map is None:
        result_map = {}

    if isinstance(obj, dict):
        for k, v in obj.items():
            lower_k = str(k).lower()

            # 1. Map the raw key (e.g., "region" -> "ASIA")
            result_map[lower_k] = v

            # 2. Map the dotted path (e.g., "sqlresults.region" -> "ASIA")
            dotted_path = f"{prefix}.{lower_k}" if prefix else lower_k
            result_map[dotted_path] = v

            # Recurse further down if it's a nested dict or list
            flatten_to_lowercase_keys(v, dotted_path, result_map)

    elif isinstance(obj, list):
        for index, item in enumerate(obj):
            dotted_path = f"{prefix}.{index}" if prefix else str(index)
            flatten_to_lowercase_keys(item, dotted_path, result_map)

    return result_map

def interpolate_string(text: str, incident: dict, inv_context: dict, platform: str, args: dict, remove_not_found: str, match_map: dict) -> tuple:
    """
    Core logic to interpolate placeholders in a single string.
    Returns: (interpolated_text: str, has_placeholders: bool)
    """
    if not isinstance(text, str):
        return text, False

    reg = r'\${(.+?)}'
    mapping = {}
    XSIAM = 'x2'

    # Check if there are any variables to replace at all
    if not re.search(reg, text):
        return text, False

    # 1. Scan the string and build a map of values
    for match in re.finditer(reg, text):
        path = match.group(1)
        lower_path = path.lower()

        # Handle XSOAR Incident Labels
        if path.startswith('incident.labels.') and platform != XSIAM:
            mapping[path] = get_label(incident, path)

        # Handle XSOAR Incident Fields (and Custom Fields fallback)
        elif path.startswith('incident.') and platform != XSIAM:
            mapping[path] = demisto.dt({'incident': incident}, path)
            if mapping[path] is None:
                custom_field_path = path.replace('incident.', 'incident.CustomFields.', 1)
                mapping[path] = demisto.dt({'incident': incident}, custom_field_path)

        # Handle XSIAM Issue Labels
        elif path.startswith('issue.labels.') and platform == XSIAM:
            mapping[path] = get_label(incident, path)

        # Handle XSIAM Issue Fields (and Custom Fields fallback)
        elif path.startswith('issue.') and platform == XSIAM:
            mapping[path] = demisto.dt({'issue': incident}, path)
            if mapping[path] is None:
                custom_field_path = path.replace('issue.', 'issue.CustomFields.', 1)
                mapping[path] = demisto.dt({'issue': incident}, custom_field_path)

        # Handle explicit Object provided in args
        elif path.startswith('object.'):
            obj_arg = args.get('object', {})
            if isinstance(obj_arg, str):
                try:
                    obj = json.loads(obj_arg)
                except ValueError:
                    obj = {}
            else:
                obj = obj_arg
            mapping[path] = demisto.dt({'object': obj}, path)

        # NEW: Handle Match Object (Case-Insensitive & Flattened)
        elif match_map and lower_path in match_map:
            mapping[path] = match_map[lower_path]

        # Handle General Context
        else:
            mapping[path] = demisto.dt(inv_context, path)

    # 2. Replace placeholders with mapped values
    for path, val in mapping.items():
        placeholder = f'${{{path}}}'
        if val is not None:
            val_to_insert = json.dumps(val) if isinstance(val, (dict, list)) else str(val)
            text = text.replace(placeholder, val_to_insert)
        elif remove_not_found == 'yes':
            text = text.replace(placeholder, '')

    return text, True

def main():
    args = demisto.args()
    input_string = args.get('inputString', '')
    input_dict_arg = args.get('inputDict', '')
    match_object_arg = args.get('matchObject', '')
    base_key = args.get('key', 'PopulatePlaceholders')
    remove_not_found = args.get('removeNotFound', 'no')

    platform = demisto.demistoVersion().get('platform', '')

    incidents = demisto.incidents()
    incident = incidents[0] if incidents else {}
    inv_context = demisto.context()

    # --- Prepare the Match Object ---
    match_map = {}
    if match_object_arg:
        if isinstance(match_object_arg, str):
            try:
                match_object = json.loads(match_object_arg)
            except Exception as e:
                return_error(f"Failed to parse matchObject as JSON: {e}")
        else:
            match_object = match_object_arg

        # Flatten the object and convert all keys/paths to lowercase
        match_map = flatten_to_lowercase_keys(match_object)

    context_outputs = {}
    human_readable_entries = []

    # --- 1. Process Dictionary Input (Bulk) ---
    if input_dict_arg:
        if isinstance(input_dict_arg, str):
            try:
                input_dict = json.loads(input_dict_arg)
            except Exception as e:
                return_error(f"Failed to parse inputDict as JSON: {e}")
        else:
            input_dict = input_dict_arg

        for dict_key, dict_value in input_dict.items():
            interpolated_text, was_modified = interpolate_string(
                dict_value, incident, inv_context, platform, args, remove_not_found, match_map
            )

            if was_modified:
                context_outputs[dict_key] = interpolated_text
                human_readable_entries.append(f"- **{base_key}.{dict_key}**: {interpolated_text}")

    # --- 2. Process Single String Input ---
    elif input_string:
        interpolated_text, was_modified = interpolate_string(
            input_string, incident, inv_context, platform, args, remove_not_found, match_map
        )
        context_outputs = interpolated_text
        human_readable_entries.append(f"- **{base_key}**: {interpolated_text}")

    # --- 3. Return via CommandResults ---
    if not context_outputs and not human_readable_entries:
        human_readable = "No placeholders found to interpolate in the provided input, or input was empty. Skipping."
        return_results(CommandResults(readable_output=human_readable))
        return

    human_readable = "### Interpolation Results Saved to Context\n" + "\n".join(human_readable_entries)

    results = CommandResults(
        outputs_prefix=base_key,
        outputs=context_outputs,
        readable_output=human_readable
    )

    return_results(results)

if __name__ in ('__main__', '__builtin__', 'builtins'):
    main()
