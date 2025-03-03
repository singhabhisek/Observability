import os
import requests
import zipfile
import shutil

class LRResultsDownloader:
    def __init__(self, server_url, domain, project, username, password):
        """
        Initializes the downloader with authentication.
        :param server_url: Base URL of the Performance Center API.
        :param domain: ALM domain name.
        :param project: ALM project name.
        :param username: Username for authentication.
        :param password: Password for authentication.
        """
        self.server_url = server_url
        self.domain = domain
        self.project = project
        self.session = requests.Session()
        self.session.auth = (username, password)
        self.session.headers.update({"Content-Type": "application/json"})

        # Base directory for storing results
        self.base_dir = "LRResults"
        os.makedirs(self.base_dir, exist_ok=True)

    def check_run_status(self, run_id):
        """
        Checks if the test run is finished or pending analysis.
        :param run_id: Test run ID.
        :return: True if the test is collated, False otherwise.
        """
        run_status_url = f"{self.server_url}/LoadTest/rest/domains/{self.domain}/projects/{self.project}/Runs/{run_id}"
        response = self.session.get(run_status_url)

        if not response.ok:
            print(f"Error fetching test run status for {run_id}")
            return False

        run_data = response.text  # XML response from Performance Center

        # Check for valid run states
        if "<RunState>Finished</RunState>" in run_data or "<RunState>Pending Creating Analysis Data</RunState>" in run_data:
            print(f"Run {run_id} is ready for result extraction.")
            return True
        else:
            print(f"Test {run_id} is not collated. Please collate the results.")
            return False

    def clean_folder(self, folder_path):
        """Removes and recreates a clean folder."""
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)
        os.makedirs(folder_path)

    def download_results_zip(self, run_id):
        """
        Downloads `Results_<run_id>.zip` and saves it in `LRResults/`, only if the test is collated.
        :param run_id: Test run ID.
        :return: Path to the extracted results folder or None if the test is not collated.
        """
        if not self.check_run_status(run_id):
            return None  # Exit if the test is not collated

        test_dir = os.path.join(self.base_dir, str(run_id))
        self.clean_folder(test_dir)  # Ensure a clean directory

        results_zip_name = f"Results_{run_id}.zip"
        zip_path = os.path.join(test_dir, results_zip_name)

        # Fetch test metadata
        response = self.session.get(f"{self.server_url}/Runs/{run_id}/Results")
        if not response.ok:
            print(f"Error fetching metadata for run ID {run_id}")
            return None

        test_results = response.json()
        file_id = None

        # Find the matching ZIP file
        for file in test_results:
            if file['Name'] == results_zip_name:
                file_id = str(file['ID'])
                break

        if not file_id:
            print(f"{results_zip_name} not found for run ID {run_id}")
            return None

        # Download ZIP file
        req = self.session.get(f"{self.server_url}/Runs/{run_id}/Results/{file_id}/data")
        if req.ok:
            with open(zip_path, 'wb') as f:
                f.write(req.content)
            print(f"Downloaded {results_zip_name} to {test_dir}")

            # Extract ZIP file
            extract_path = os.path.join(test_dir, "Extracted")
            os.makedirs(extract_path, exist_ok=True)

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)

            print(f"Extracted to: {extract_path}")

            # Remove ZIP file after extraction
            os.remove(zip_path)
            print(f"Deleted ZIP file: {zip_path}")

            return extract_path
        else:
            print(f"Failed to download {results_zip_name}")
            return None


# Initialize the downloader with server details
downloader = LRResultsDownloader(
    "https://example.com/api", "MyDomain", "MyProject", "user", "pass"
)

# Call with just the run_id
results_path = downloader.download_results_zip(2099)

print(f"Results saved at: {results_path}")

=====================================================


import os
import requests
import zipfile
import shutil
import pyodbc

class LRResultsDownloader:
    def __init__(self, server_url, domain, project, username, password):
        """
        Initializes the downloader with authentication.
        :param server_url: Base URL of the Performance Center API.
        :param domain: ALM domain name.
        :param project: ALM project name.
        :param username: Username for authentication.
        :param password: Password for authentication.
        """
        self.server_url = server_url
        self.domain = domain
        self.project = project
        self.session = requests.Session()
        self.session.auth = (username, password)
        self.session.headers.update({"Content-Type": "application/json"})

        # Base directory for storing results
        self.base_dir = "LRResults"
        os.makedirs(self.base_dir, exist_ok=True)

    def check_run_status(self, run_id):
        """Checks if the test run is finished or pending analysis."""
        run_status_url = f"{self.server_url}/LoadTest/rest/domains/{self.domain}/projects/{self.project}/Runs/{run_id}"
        response = self.session.get(run_status_url)

        if not response.ok:
            print(f"Error fetching test run status for {run_id}")
            return False

        run_data = response.text  # XML response from Performance Center

        if "<RunState>Finished</RunState>" in run_data or "<RunState>Pending Creating Analysis Data</RunState>" in run_data:
            print(f"Run {run_id} is ready for result extraction.")
            return True
        else:
            print(f"Test {run_id} is not collated. Please collate the results.")
            return False

    def clean_folder(self, folder_path):
        """Removes and recreates a clean folder."""
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)
        os.makedirs(folder_path)

    def download_results_zip(self, run_id):
        """Downloads and extracts `Results_<run_id>.zip`, then deletes the ZIP file."""
        if not self.check_run_status(run_id):
            return None  

        test_dir = os.path.join(self.base_dir, str(run_id))
        self.clean_folder(test_dir)

        results_zip_name = f"Results_{run_id}.zip"
        zip_path = os.path.join(test_dir, results_zip_name)

        # Fetch test metadata
        response = self.session.get(f"{self.server_url}/Runs/{run_id}/Results")
        if not response.ok:
            print(f"Error fetching metadata for run ID {run_id}")
            return None

        test_results = response.json()
        file_id = None

        # Find the matching ZIP file
        for file in test_results:
            if file['Name'] == results_zip_name:
                file_id = str(file['ID'])
                break

        if not file_id:
            print(f"{results_zip_name} not found for run ID {run_id}")
            return None

        # Download ZIP file
        req = self.session.get(f"{self.server_url}/Runs/{run_id}/Results/{file_id}/data")
        if req.ok:
            with open(zip_path, 'wb') as f:
                f.write(req.content)
            print(f"Downloaded {results_zip_name} to {test_dir}")

            # Extract ZIP file
            extract_path = os.path.join(test_dir, "Extracted")
            os.makedirs(extract_path, exist_ok=True)

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)

            print(f"Extracted to: {extract_path}")

            # Remove ZIP file after extraction
            os.remove(zip_path)
            print(f"Deleted ZIP file: {zip_path}")

            return extract_path
        else:
            print(f"Failed to download {results_zip_name}")
            return None

    def query_mdb(self, run_id, sql_query):
        """
        Connects to `results_<run_id>.mdb` and executes the given SQL query.
        :param run_id: Test run ID.
        :param sql_query: SQL query to execute.
        :return: Query result rows.
        """
        extracted_path = os.path.join(self.base_dir, str(run_id), "Extracted")
        mdb_path = os.path.join(extracted_path, f"results_{run_id}.mdb")

        if not os.path.exists(mdb_path):
            print(f"MDB file not found: {mdb_path}")
            return None

        try:
            # Connecting to the MDB file
            conn_str = r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=" + mdb_path + ";"
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()

            cursor.execute(sql_query)
            rows = cursor.fetchall()

            cursor.close()
            conn.close()

            return rows
        except Exception as e:
            print(f"Error executing query on {mdb_path}: {e}")
            return None



==================================================


# Initialize downloader
downloader = LRResultsDownloader(
    "https://example.com/api", "MyDomain", "MyProject", "user", "pass"
)

# Download results and extract
extract_path = downloader.download_results_zip(2099)

# Query the MDB file
if extract_path:
    query = "SELECT * FROM Transactions"  # Example query
    results = downloader.query_mdb(2099, query)

    if results:
        for row in results:
            print(row)
    else:
        print("No data found in the query.")
