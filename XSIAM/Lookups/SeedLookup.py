import json
import time
import traceback
from typing import Dict, Any, List

class XSIAMQueryManager:
    """
    Manages the execution and retrieval of XQL queries via the Core REST API in XSIAM.
    """

    def __init__(self, source_using: str):
        self.source_using = source_using
        self.start_query_uri = "/public_api/v1/xql/start_xql_query"
        self.get_results_uri = "/public_api/v1/xql/get_query_results"

    def _execute_api_post(self, uri: str, body: dict, instance_name: str) -> dict:
        """
        Helper method to execute the core-api-post command.
        """
        command_args = {
            "uri": uri,
            "body": json.dumps(body),
            "using": instance_name
        }

        res = demisto.executeCommand("core-api-post", command_args)

        if isError(res[0]):
            raise Exception(f"API Request failed on {uri}: {res[0].get('Contents')}")

        return res[0].get('Contents', {}).get('response', {})

    def start_query(self, query: str, time_from: int, time_to: int) -> str:
        """
        Starts an XQL query on the production server (source_using) within a specific timeframe
        and returns the execution ID.
        """
        body = {
            "request_data": {
                "query": query,
                "tenants": [],
                "timeframe": {
                    "from": time_from,
                    "to": time_to
                }
            }
        }

        demisto.debug(f"Starting XQL query on prod instance: {self.source_using} between {time_from} and {time_to}")
        response = self._execute_api_post(self.start_query_uri, body, self.source_using)

        query_id = response.get("reply")
        if not query_id:
            raise Exception("Failed to retrieve query execution ID from response.")

        return query_id

    def get_query_results(self, query_id: str, max_retries: int = 30, sleep_interval: int = 5) -> List[Dict[str, Any]]:
        """
        Polls the API for query results until it succeeds, fails, or times out.
        Returns the raw data payload for all matching rows. Limit should be defined in the XQL query by the user.
        """
        body = {
            "request_data": {
                "query_id": query_id,
                "pending_jobs_timeout": 0
            }
        }

        for attempt in range(max_retries):
            demisto.debug(f"Polling query results for ID {query_id} (Attempt {attempt + 1}/{max_retries})")
            response = self._execute_api_post(self.get_results_uri, body, self.source_using)

            reply = response.get("reply", {})
            status = reply.get("status", "")

            if status == "SUCCESS":
                return reply.get("results", {}).get("data", [])
            elif status in ["PENDING", "RUNNING"]:
                time.sleep(sleep_interval)
            else:
                raise Exception(f"Query execution failed or reached an unknown state: {status}")

        raise Exception("Query results polling timed out.")


class DataProcessor:
    """
    Handles the transformation of raw XQL results into the cleaned schema.
    """

    def __init__(self):
        self.excluded_columns = {"_insert_time", "_time"}

    def process_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Iterates over all results, drops specific time columns,
        and renames any columns starting with an underscore.
        """
        if not data:
            return []

        processed_data = []

        for row in data:
            processed_row = {}
            for key, value in row.items():
                # Requirement: Drop the _insert_time and _time columns
                if key in self.excluded_columns:
                    continue

                # Requirement: rename any other column names that have a leading underscore
                new_key = key.lstrip("_") if key.startswith("_") else key

                processed_row[new_key] = value

            processed_data.append(processed_row)

        return processed_data

    def mask_values(self, data: Any, placeholder_text: str = "placeholder") -> Any:
        """
        Recursively iterates through dictionaries and lists to replace all underlying
        primitive values with a designated placeholder string.
        """
        if isinstance(data, dict):
            return {k: self.mask_values(v, placeholder_text) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.mask_values(item, placeholder_text) for item in data]
        else:
            return placeholder_text


def main():
    try:
        # Retrieve arguments
        args = demisto.args()
        source_using = args.get('source_using')
        xql_query = args.get('xql_query')
        time_from_raw = args.get('time_from')
        time_to_raw = args.get('time_to')

        # Ensure timestamps are integers (epoch milliseconds)
        try:
            time_from = int(time_from_raw)
            time_to = int(time_to_raw)
        except ValueError:
            return_error("Invalid argument type: 'time_from' and 'time_to' must be integers representing epoch milliseconds.")

        # Initialize the classes
        query_manager = XSIAMQueryManager(source_using=source_using)
        processor = DataProcessor()

        # 1. Start the query on the prod system with the timeframe
        query_id = query_manager.start_query(xql_query, time_from, time_to)

        # 2. Retrieve all results
        raw_data = query_manager.get_query_results(query_id)

        if not raw_data:
            return_results("Query executed successfully but returned 0 rows. No files generated.")
            return

        # 3. Process the data (drop/rename columns across the whole dataset)
        processed_data = processor.process_data(raw_data)

        # 4. Create Seed File (Index 0 only) and return to WarRoom
        # Mask the values of the first row with "placeholder"
        masked_seed_row = processor.mask_values(processed_data[0], placeholder_text="placeholder")

        # Ensure it's a completely flat dictionary (no list wrapper `[]`, no indentation)
        seed_content = json.dumps(masked_seed_row)
        seed_file_result = fileResult(filename="seed_file.json", data=seed_content)
        return_results(seed_file_result)

        # 5. Create Data File (All rows) and return to WarRoom
        # Keeping this indented so it remains a readable bulk JSON file
        data_content = json.dumps(processed_data, indent=4)
        data_file_result = fileResult(filename="data.json", data=data_content)
        return_results(data_file_result)

    except Exception as e:
        demisto.error(traceback.format_exc())
        return_error(f"Failed to execute script. Error: {str(e)}")


if __name__ in ("__main__", "__builtin__", "builtins"):
    main()
