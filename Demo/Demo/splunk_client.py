import requests  # Import requests module to handle HTTP requests
import os  # Import os module to interact with the file system
from datetime import datetime, timedelta  # Import datetime functions to work with timestamps
from pathlib import Path

 # Define the base directory where mock data files are stored
    # Get the base directory (where the script is located)
SCRIPT_DIR = Path(__file__).resolve().parent
MOCK_DATA_DIR = SCRIPT_DIR / "static" / "mock_data1"

class SplunkAPI:
    """
    A class to interact with Splunk REST API.
    It can execute queries on a live Splunk instance and read mock data files for testing.
    """


    
    def __init__(self, host, username, password):
        """
        Initialize the Splunk API class with authentication details.

        Parameters:
        host (str): Splunk server URL.
        username (str): Splunk login username.
        password (str): Splunk login password.
        """
        self.host = host  # Store Splunk host URL
        self.auth = (username, password)  # Store authentication credentials
        self.headers = {"Content-Type": "application/x-www-form-urlencoded"}  # Set HTTP headers for requests

    def execute_query(self, query):
        """
        Execute a Splunk search query and return results.

        Parameters:
        query (str): Splunk search query.

        Returns:
        dict: Query results or an error message.
        """
        # Define the Splunk API endpoint for search jobs
        url = f"{self.host}/services/search/jobs"

        # Set the data payload for the search request
        data = {
            "search": f"search {query}",
            "output_mode": "json",  # Request JSON output format
            "exec_mode": "blocking"  # Ensure the query completes before returning
        }

        # Send a POST request to start a search job
        response = requests.post(url, auth=self.auth, headers=self.headers, data=data, verify=False)

        # Check if the request was successful
        if response.status_code != 201:
            return {"error": f"Failed to submit query: {response.text}"}  # Return error message if failed

        # Extract the search job ID from the response
        job_id = response.json().get("sid")

        # Define the API endpoint to retrieve search results
        results_url = f"{self.host}/services/search/jobs/{job_id}/results?output_mode=json"

        # Send a GET request to fetch the search results
        results_response = requests.get(results_url, auth=self.auth, verify=False)

        # Check if the request was successful
        if results_response.status_code != 200:
            return {"error": f"Failed to fetch results: {results_response.text}"}  # Return error message if failed

        # Return the search results
        return results_response.json().get("results", [])
    
   

    
    

    @staticmethod
    def read_mock_data(file_path, start_time, end_time):
        """
        Reads a mock data file and filters entries within a given time range.

        Parameters:
        file_path (str): Path to the mock data file.
        start_time (datetime): Start of the time range.
        end_time (datetime): End of the time range.

        Returns:
        list: Filtered list of log entries.
        """

        file_path = MOCK_DATA_DIR / file_path  # Construct full path dynamically

        # Check if the file exists
        if not os.path.exists(file_path):
            return {"error": f"Mock data file {file_path} not found"}  # Return error if file is missing

        # Open the file and read all lines
        with open(file_path, "r") as file:
            lines = file.readlines()

        # Check if the file has enough data (at least a header and one data row)
        if len(lines) < 2:
            return {"error": "File is empty or missing data"}

        # Extract column names from the first row (header)
        headers = lines[0].strip().split("\t")

        # Identify the timestamp column
        timestamp_col = next((col for col in headers if col.lower() in {"timestamp", "time", "log_time"}), None)

        # Return error if no valid timestamp column is found
        if not timestamp_col:
            return {"error": "No valid timestamp column found"}

        data = []  # Initialize a list to store filtered results

        # Convert start and end times to string format for easy comparison
        start_time_str = start_time #.strftime("%Y-%m-%d %H:%M")
        end_time_str = end_time #.strftime("%Y-%m-%d %H:%M")

        # Loop through each data row (excluding the header)
        for line in lines[1:]:
            # Split the line into individual fields based on tab delimiter
            parts = line.strip().split("\t", maxsplit=len(headers) - 1)

            # Ensure the number of fields matches the header count
            if len(parts) == len(headers):
                # Extract timestamp field
                timestamp_str = parts[headers.index(timestamp_col)]
                # print(start_time_str, timestamp_str ,end_time_str)
                # try:
                #     # Convert timestamp string to datetime object
                #     timestamp_dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                # except ValueError:
                #     continue  # Skip row if timestamp format is incorrect
                # print(start_time_str, timestamp_str.strftime("%Y-%m-%d %H:%M") ,end_time_str)
                # Convert timestamp to a string format without seconds
                if start_time_str <= timestamp_str <= end_time_str:
                    data.append(dict(zip(headers, parts)))  # Store valid entries

        return data  # Return filtered mock data
