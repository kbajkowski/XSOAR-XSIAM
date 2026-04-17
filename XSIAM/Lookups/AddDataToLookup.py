import csv
import json

class LookupDatasetManager:
    """
    Manages the ingestion of file data (CSV, TSV, JSON) or raw JSON payloads into XSIAM Lookup Datasets.
    """
    def __init__(self, args: dict):
        self.input_type = args.get('input_type', 'file')
        self.raw_data = args.get('raw_data', '')
        self.entry_id = args.get('entry_id')
        self.dataset_name = args.get('dataset_name')
        self.mode = args.get('mode')
        self.key_fields_arg = args.get('key_fields', '')

        self._validate_inputs()

    def _validate_inputs(self):
        """Validates the initial arguments provided to the script."""
        if self.input_type not in ['file', 'raw']:
            raise ValueError('Invalid input_type. The "input_type" argument must be strictly "file" or "raw".')

        if self.input_type == 'file' and not self.entry_id:
            raise ValueError('The "entry_id" argument is required when input_type is "file".')

        if self.input_type == 'raw' and not self.raw_data:
            raise ValueError('The "raw_data" argument is required when input_type is "raw".')

        if self.mode not in ['add_new', 'update_existing']:
            raise ValueError('Invalid mode. The "mode" argument must be strictly "add_new" or "update_existing".')

        if self.mode == 'update_existing' and not self.key_fields_arg:
            raise ValueError('The "key_fields" argument is required when mode is "update_existing" so XSIAM knows which rows to update.')

    def _get_file_info(self) -> dict:
        """Retrieves file path and metadata from the WarRoom Entry ID."""
        file_info = demisto.getFilePath(self.entry_id)
        if not file_info:
            raise ValueError(f'Could not find the file for entry ID: {self.entry_id}. Ensure the file was uploaded to the WarRoom.')
        return file_info

    def _parse_csv_tsv(self, file_path: str, delimiter: str) -> list:
        """Dedicated method to parse CSV and TSV files into a list of dictionaries."""
        parsed_data = []
        try:
            with open(file_path, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file, delimiter=delimiter)
                for row in reader:
                    parsed_data.append(row)
            return parsed_data
        except Exception as e:
            raise Exception(f'Failed to read or parse the CSV/TSV file: {str(e)}')

    def _parse_json(self, file_path: str) -> list:
        """Dedicated method to parse JSON files into a list of dictionaries."""
        try:
            with open(file_path, mode='r', encoding='utf-8') as file:
                parsed_data = json.load(file)
                if isinstance(parsed_data, dict):
                    return [parsed_data]
                elif isinstance(parsed_data, list):
                    return parsed_data
                else:
                    raise ValueError("JSON file must contain a list of dictionary objects or a single dictionary object.")
        except Exception as e:
            raise Exception(f'Failed to read or parse the JSON file: {str(e)}')

    def _parse_raw_json(self) -> list:
        """Dedicated method to parse a raw JSON string provided by the user."""
        try:
            parsed_data = json.loads(self.raw_data)
            if isinstance(parsed_data, dict):
                return [parsed_data]
            elif isinstance(parsed_data, list):
                return parsed_data
            else:
                raise ValueError("Raw JSON must be a dictionary object or a list of dictionary objects.")
        except json.JSONDecodeError as e:
            raise Exception(f'Failed to parse raw data as JSON. Ensure it is properly formatted. Error: {str(e)}')

    def extract_data_from_file(self, file_path: str, file_name: str) -> list:
        """Determines file type and routes to the appropriate parsing method."""
        file_name_lower = file_name.lower()

        if file_name_lower.endswith('.tsv'):
            return self._parse_csv_tsv(file_path, delimiter='\t')
        elif file_name_lower.endswith('.csv'):
            return self._parse_csv_tsv(file_path, delimiter=',')
        elif file_name_lower.endswith('.json'):
            return self._parse_json(file_path)
        else:
            raise ValueError(f'Unsupported file type: {file_name}. Only .csv, .tsv, and .json files are supported.')

    def _remove_system_fields(self, data: list) -> list:
        """Removes protected XSIAM system fields from the payload before ingestion."""
        fields_to_remove = ['_time', '_insert_time']
        for row in data:
            if isinstance(row, dict):
                for field in fields_to_remove:
                    row.pop(field, None)
        return data

    def _stringify_complex_types(self, data: list) -> list:
        """Converts nested arrays and dictionaries into JSON strings to match XSIAM schema."""
        for row in data:
            if isinstance(row, dict):
                for key, value in row.items():
                    if isinstance(value, (list, dict)):
                        # Stringify the nested JSON so the API accepts it as text
                        # while preserving the exact JSON structure for XQL queries
                        row[key] = json.dumps(value)
        return data

    def _build_payload(self, parsed_data: list) -> dict:
        """Constructs the JSON payload expected by the XSIAM API."""
        request_data = {
            "dataset_name": self.dataset_name,
            "data": parsed_data
        }

        if self.mode == 'update_existing':
            request_data['key_fields'] = [k.strip() for k in self.key_fields_arg.split(',')]

        return {"request_data": request_data}

    def _execute_api_call(self, payload: dict) -> dict:
        """Makes the core-api-post call and handles raw API errors."""
        uri = '/public_api/v1/xql/lookups/add_data'
        try:
            res = demisto.executeCommand('core-api-post', {
                'uri': uri,
                'body': json.dumps(payload)
            })
        except Exception as e:
            raise Exception(f"Failed to execute core-api-post command. Internal error: {str(e)}")

        if isError(res):
            error_message = get_error(res)
            raise Exception(f'API Call failed: {error_message}')

        return res[0].get('Contents', {})

    def _process_response(self, response_data: any, input_source_name: str) -> CommandResults:
        """Parses the API response, handles logical errors, and builds the command results."""
        if isinstance(response_data, str):
            try:
                response_data = json.loads(response_data)
            except json.JSONDecodeError:
                pass

        if isinstance(response_data, dict):
            reply = response_data.get('response', response_data).get('reply', {})

            if 'err_code' in reply or 'err_msg' in reply:
                 err_code = reply.get('err_code', 'UNKNOWN_CODE')
                 err_msg = reply.get('err_msg', 'No error message provided by API.')
                 err_extra = reply.get('err_extra', '')
                 raise Exception(f"XSIAM API Error ({err_code}): {err_msg} | Additional Info: {err_extra}")

            added = reply.get('rows added', 0)
            updated = reply.get('rows updated', 0)
            skipped = reply.get('rows skipped', 0)

            md_output = f"### Successfully updated lookup dataset: `{self.dataset_name}`\n"
            md_output += f"* **Input Source**: `{input_source_name}`\n"
            md_output += f"* **Added**: {added} rows\n* **Updated**: {updated} rows\n* **Skipped**: {skipped} rows\n"

            return CommandResults(
                readable_output=md_output,
                outputs_prefix='AddDataToLookup.LookupDataset',
                outputs_key_field='dataset_name',
                outputs={'dataset_name': self.dataset_name, 'added': added, 'updated': updated, 'skipped': skipped}
            )
        else:
            raise Exception(f"Unexpected response format from API: {response_data}")

    def run(self) -> CommandResults:
        """Main orchestration method to execute the ingestion process."""
        # 1. Determine input source and extract data
        if self.input_type == 'file':
            file_info = self._get_file_info()
            input_source_name = file_info['name']
            parsed_data = self.extract_data_from_file(file_info['path'], input_source_name)
        elif self.input_type == 'raw':
            input_source_name = "Raw JSON Input"
            parsed_data = self._parse_raw_json()

        if not parsed_data:
            raise ValueError('The provided data appears to be empty or lacks valid formatting.')

        # 2. Scrub system fields to prevent API errors
        parsed_data = self._remove_system_fields(parsed_data)

        # 3. Stringify complex JSON arrays/objects to pass XSIAM schema validation
        parsed_data = self._stringify_complex_types(parsed_data)

        # 4. Build Payload
        payload = self._build_payload(parsed_data)

        # 5. Execute Call
        raw_response = self._execute_api_call(payload)

        # 6. Process and Return Results
        return self._process_response(raw_response, input_source_name)

def main():
    try:
        manager = LookupDatasetManager(demisto.args())
        results = manager.run()
        return_results(results)
    except Exception as e:
        return_error(f"Script Execution Error: {str(e)}")

if __name__ in ('__main__', '__builtin__', 'builtins'):
    main()
