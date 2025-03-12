# Import the requests library to make HTTP requests
import csv
import io
import requests

# Disable SSL warnings for unverified HTTPS requests (not recommended for production use)
requests.packages.urllib3.disable_warnings()


# Define a class to interact with the Dynatrace API
class Dynatrace:
    def __init__(self, host, token, fiddler=False):
        """
        Initialize the Dynatrace API client.
        
        :param host: Dynatrace environment URL (e.g., https://your-dynatrace-env.live.dynatrace.com)
        :param token: API token for authentication
        :param fiddler: Boolean flag to enable Fiddler proxy for debugging (default is False)
        """
        
        # Store Dynatrace host URL and API token
        self.host = host
        self.token = token

        # Create a persistent session object for making requests
        self.session = requests.Session()
        
        # Disable SSL verification (use with caution; recommended to enable in production)
        self.session.verify = False

        # Set up authentication headers for API requests
        self.session.headers.update(
            {
                "Authorization": f"Api-Token {self.token}",  # Use API token for authentication
                "Content-Type": "application/json",  # Specify that we are sending JSON data
                "Accept": "application/json",  # Expect JSON responses
            }
        )

        # If Fiddler debugging is enabled, configure proxy settings
        if fiddler:
            self.session.proxies = {
                "http": "http://127.0.0.1:8888",  # HTTP proxy for Fiddler
                "https": "http://127.0.0.1:8888",  # HTTPS proxy for Fiddler
            }

    def get_hosts_by_management_zone(self, mz_name):
        """
        Fetch all hosts (servers) within a specified management zone in Dynatrace.
        
        :param mz_name: Name of the management zone to filter hosts
        :return: Dictionary mapping host IDs to their display names
        """
        
        # Construct the API request URL with the entity selector for hosts in the given management zone
        url = f"{self.host}/api/v2/entities?entitySelector=type(\"HOST\"),mzName(\"{mz_name}\")"

        # Send a GET request to fetch hosts
        response = self.session.get(url)

        print(response.text)

        # If the request is successful (status code 200), parse and return the host data
        if response.status_code == 200:
            return {
                host["entityId"]: host["displayName"]  # Map entity IDs to their display names
                for host in response.json().get("entities", [])  # Extract host entities from response
            }

        # Return an empty dictionary if the request fails
        return {}

    def get_metrics(self, entity_ids, metric_keys, start_time, end_time, granularity="5m", response_format="json"):
        """
        Fetch CPU, memory, and application-specific metrics from Dynatrace for given entities.
        
        :param entity_ids: List of entity IDs (servers) to fetch metrics for
        :param metric_keys: Comma-separated metric IDs to retrieve
        :param start_time: Start time for the query (e.g., "now-1h")
        :param end_time: End time for the query (e.g., "now")
        :param granularity: Data resolution (default is "5m" for 5-minute intervals)
        :param response_format: Format of response ("json" or "csv"), default is "json"
        :return: JSON object if response_format is "json", CSV text if "csv", or an empty list if request fails
        """
        print('====================')
        print(entity_ids)
        print('XXXXX====================')
        # Validate response format (must be "json" or "csv")
        if response_format not in ["json", "csv"]:
            raise ValueError("Invalid response format. Choose 'json' or 'csv'.")

        # Ensure entity_ids is a list
        if isinstance(entity_ids, str):  
            entity_ids = [entity_ids]  # Convert single string to a list

        # Build the entity selector query
        entity_selector = ",".join(f'entityId("{eid}")' for eid in entity_ids)
        # # Build the entity selector query by combining entity IDs
        # entity_selector = ",".join(f'entityId("{eid}")' for eid in entity_ids)

        # Construct the API request URL for querying metrics
        url = (f"{self.host}/api/v2/metrics/query?"
            f"metricSelector={metric_keys}&entitySelector={entity_selector}"
            f"&from={start_time}&to={end_time}&resolution={granularity}")
        
        print(url)

        # Set appropriate headers based on requested response format
        headers = {
            "Authorization": f"Api-Token {self.token}",  # Authenticate with API token
            "Accept": "application/json" if response_format == "json" else "text/csv; header=present; charset=utf-8",  # Request JSON or CSV
        }

        # Send the GET request
        response = self.session.get(url, headers=headers)
        
        # Convert response text to a file-like object
        csv_data = io.StringIO(response.text)

        # Read CSV
        reader = csv.reader(csv_data)
        header = next(reader)  # Read the header row (optional)
        print(header)  # Print header if needed

        # Print the first 3 rows
        for i, row in enumerate(reader):
            if i == 3:  # Stop after 3 rows
                break
            print(row)


        # Return parsed JSON if JSON format is requested and response is successful
        if response_format == "json":
            return response.json() if response.status_code == 200 else {}

        # Return raw CSV text if CSV format is requested and response is successful
        return response.text if response.status_code == 200 else []

