register_module_line('CriblAPI', 'start', __line__())

    demisto.debug('pack id = CriblAPI, pack version = 1.0.0')

    import json
    from typing import Any
    import dateparser
    import time

    """ CONSTANTS """
    LOG_LINE = "CriblAPIDebugLog: "

    class Client(BaseClient):
        def get_token(self, client_id: str, client_secret: str) -> dict:
            """
            Retrieves bearer token, sets the expiration in the integration context
            """

            auth_url = "https://login.cribl.cloud/oauth/token"
            body = {
                    "grant_type": "client_credentials",
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "audience": "https://api.cribl.cloud"
                }

            response = self._http_request(
                method="POST",
                full_url=auth_url,
                json_data=body
            )
            return response

        def get_worker_groups_all(self, token: str) -> dict:
            """
            Retrieves information related to all worker groups.
            """
            response = self._http_request(
                method="GET",
                url_suffix = "/master/groups",
                headers={
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                }
            )
            return response

        def get_system_inputs(self,token: str, worker_group_name: str) -> dict:
            """
            Retrieves input information related to a specific worker group"
            """
            response = self._http_request(
            method="GET",
            url_suffix = f"m/{worker_group_name}/system/inputs/",
            headers={
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                }
            )
            return response


    """ HELPER FUNCTIONS """

    def is_token_expired(expiry_timestamp: int, buffer_seconds: int = 60) -> bool:
        """
        Returns True if the current time is within X seconds of the expiry.
        """
        return int(time.time()) >= (expiry_timestamp - buffer_seconds)

    def create_expiry_timestamp(expiry: int) -> int:
        """
        Creates a timestamp (in seconds) to assist in calculating expiration of the token."
        """
        return int(time.time() + expiry)

    """ COMMAND FUNCTIONS """

    def get_token_command(client: Client, client_id: str, client_secret: str) -> CommandResults:
        # Call the client method
        token = client.get_token(client_id, client_secret)

        if not token:
            raise ValueError("No access token found in the response.")

        # Format the output for the War Room
        readable_output = f"Success\nToken successfully retrieved: `{token[:10]}...[REDACTED]`"
        return readable_output


    # def test_module(client: Client, params: dict[str, Any]) -> str:
    #     """
    #     Tests API connectivity and authentication'
    #     When 'ok' is returned it indicates the integration works like it is supposed to and connection to the service is
    #     successful.
    #     Raises exceptions if something goes wrong.

    #     Args:
    #         client (Client): HelloWorld client to use.
    #         params (Dict): Integration parameters.
    #         first_fetch_time (int): The first fetch time as configured in the integration params.

    #     Returns:
    #         str: 'ok' if test passed, anything else will raise an exception and will fail the test.
    #     """

    #     # INTEGRATION DEVELOPER TIP
    #     # Client class should raise the exceptions, but if the test fails
    #     # the exception text is printed to the Cortex UI.
    #     # If you have some specific errors you want to capture (i.e. auth failure)
    #     # you should catch the exception here and return a string with a more
    #     # readable output (for example return 'Authentication Error, API Key
    #     # invalid').
    #     # Cortex will print everything you return different than 'ok' as
    #     # an error
    #     try:
    #         time = dateparser.parse("1 minute")
    #         assert time
    #         severity = params.get("severity", None)
    #         if params.get("isFetch"):  # Tests fetch alert:
    #             fetch_incidents(client=client, max_results=1, last_run={}, first_fetch_time=time.isoformat(), severity=severity)
    #         else:
    #             client.get_alert_list(limit=1, severity=params.get("severity"))

    #     except DemistoException as e:
    #         if "Forbidden" in str(e):
    #             return "Authorization Error: make sure API Key is correctly set"
    #         else:
    #             raise e

    #     return "ok"

    """ MAIN FUNCTION """

    def main() -> None:
        params = demisto.params()
        command = demisto.command()
        client_id = params.get("credentials", {}).get("identifier")
        client_secret = params.get("credentials", {}).get("password")

        client = Client(
            base_url=params.get("url"),
            verify=not params.get("insecure", False),
            proxy=params.get("proxy", False)
        )

        # Check for valid token
        integration_context = get_integration_context()
        token = integration_context.get("token",None)
        token_expiry = integration_context.get("expiry",None)

        # Get new token if existing is expired/doesn't exist
        if not token or is_token_expired(token_expiry):
            token_data = client.get_token(client_id,client_secret)
            token = token_data.get("access_token")
            expiry = token_data.get("expires_in")
            expiry_timestamp = create_expiry_timestamp(expiry)
            set_integration_context({
                'token': token,
                'expiry': expiry_timestamp
            })

        # Command Seciton
        try:
            if command == "test-module":
                # Probably need to change this logic because get_token doesn't hit the same set of endpoints that the rest of the API calls would
                client.get_token(client_id, client_secret)
                return_results("ok")

            elif command == "cribl-get-all-worker-groups":
                response = client.get_worker_groups_all(token)
                command_results = CommandResults(
                    outputs_prefix='Cribl.WorkerGroups',
                    readable_output=f"Response can be found in the context data under Cribl.WorkerGroups.",
                    outputs = response
                )
                return_results(command_results)

            elif command == "cribl-get-system-inputs":
                worker_group = demisto.args().get('worker_group_name')
                response = client.get_system_inputs(token,worker_group)
                command_results = CommandResults(
                    outputs_prefix=f'Cribl.SystemInputs.{worker_group}',
                    readable_output=f"Response can be found in the context data under Cribl.SystemInputs.{worker_group}.",
                    outputs = response
                )
                return_results(command_results)

        except Exception as e:
            return_error(f"Error: {str(e)}")


    """ ENTRY POINT """

    if __name__ in ("__main__", "__builtin__", "builtins"):
        main()

register_module_line('CriblAPI', 'end', __line__())
