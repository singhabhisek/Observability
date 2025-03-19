from io import StringIO
import requests
import streamlit as st
import pandas as pd
import numpy as np

import json
import os
import random
import plotly.express as px
from datetime import datetime, time, timedelta
import time
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
from splunk_client import SplunkAPI

from dynatrace_client import Dynatrace  # Import the Dynatrace client from a separate file

# from streamlit_date_picker import date_range_picker, date_picker, PickerType
# from streamlit_datetime_range_picker import datetime_range_picker


splunk = SplunkAPI("test.com","abcd","def")


# Load Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
STATIC_FOLDER = os.path.join(BASE_DIR, "static")

with open(CONFIG_PATH, "r") as config_file:
    config = json.load(config_file)

APPLICATIONS = list(config.get("applications", {}).keys())


APPLICATIONS = list(config.get("applications", {}).keys())
DT_ENVIRONMENT = config["dynatrace"]["environment"]
DT_API_TOKEN = config["dynatrace"]["api_token"]
HEADERS = {"Authorization": f"Api-Token {DT_API_TOKEN}", "Content-Type": "application/json"}

dt_client = Dynatrace(DT_ENVIRONMENT, DT_API_TOKEN)


# Extract Splunk details
SPLUNK_HOST = config["splunk"]["host"]
SPLUNK_PORT = config["splunk"]["port"]
SPLUNK_USERNAME = config["splunk"]["username"]
SPLUNK_PASSWORD = config["splunk"]["password"]
SPLUNK_INDEX = config["splunk"]["index"]

# Initialize session state
if "fetch_data_clicked" not in st.session_state:
    st.session_state.fetch_data_clicked = False

# Initialize df_pivot as an empty DataFrame to prevent NameError
df_pivot = pd.DataFrame()

test_scenarios = {
    "OOLB": [
        {"testID": "T001", "testScenarioName": "Login Test"},
        {"testID": "T002", "testScenarioName": "Payment Test"}
    ],
    "Mobile": [
        {"testID": "T101", "testScenarioName": "App Launch Test"},
        {"testID": "T102", "testScenarioName": "Push Notification Test"}
    ]
}


transaction_data = {
    "T001": ["Login Request", "Login Response"],
    "T002": ["Payment Initiated", "Payment Success", "Payment Failure"],
    "T101": ["App Start", "App Load", "App Crash"],
    "T102": ["Notification Received", "Notification Clicked"]
}


# Function to fetch all available Test Set IDs
def fetch_all_test_ids():
    """Simulates fetching all available test set IDs from the database."""
    return ["T001", "T002", "T101", "T102"]  # Replace with actual DB fetch logic

# Function to fetch test details dynamically
def fetch_test_details(test_id):
    """Simulates fetching test details for a given test ID from the database."""
    test_details = {
        "T001": {"start_date": "2025-03-01", "end_date": "2025-03-05", "testScenarioName": "Login Test"},
        "T002": {"start_date": "2025-03-06", "end_date": "2025-03-10", "testScenarioName": "Payment Test"},
        "T101": {"start_date": "2025-03-11", "end_date": "2025-03-15", "testScenarioName": "App Launch Test"},
        "T102": {"start_date": "2025-03-16", "end_date": "2025-03-20", "testScenarioName": "Push Notification Test"},
    }
    return test_details.get(test_id, {})  # Replace with actual DB query

# Function to fetch transaction names for a selected Test Set
def fetch_transactions_for_test(test_id):
    """Simulates fetching transactions related to a test set."""
    transaction_data = {
        "T001": ["Login Request", "Login Response"],
        "T002": ["Payment Initiated", "Payment Success", "Payment Failure"],
        "T101": ["App Start", "App Load", "App Crash"],
        "T102": ["Notification Received", "Notification Clicked"]
    }
    return transaction_data.get(test_id, [])  # Replace with actual DB query


# Generate dummy transaction data
def generate_transaction_data_lr():
    transactions = []
    for i in range(10):
        transactions.append({
            "Transaction Name": f"Transaction {i+1}",
            "Average Response Time (s)": round(random.uniform(1.0, 5.0), 2),
            "90th Percentile Response Time (s)": round(random.uniform(1.5, 6.0), 2),
            "Pass Count": random.randint(100, 500),
            "Fail Count": random.randint(0, 10)
        })
    return pd.DataFrame(transactions)

#Adjust for max Y-axis

def get_y_axis_limit(y_max):
    """
    Dynamically calculates the upper limit for the Y-axis.
    - For percentages: scale to 50% or 100%
    - For numeric values: add 5 extra intervals
    """
    if y_max <= 1:  
        return 1.0  # Scale to 100% (1.0)

    if y_max <= 50:  
        return 100  # Scale to 100% if under 50%

    if y_max <= 100:  
        return 100  # Keep at 100% if it's a percentage

    # Find the nearest rounded interval (e.g., 5000 for 25000)
    # magnitude = 10 ** (len(str(int(y_max))) - 1) if y_max > 0 else 10  # Example: 25000 → 10000
    # interval = max(magnitude // 2, 1000)  # Ensure a reasonable interval

    # Round up to the next multiple of the interval
    #new_limit = ((y_max // interval) + 1) * interval
    return y_max

# Generate Dummy Data for LoadRunner graphs - this needs to be done with real data
lr_data = [
    {"timestamp": f"2025-03-03 12:{i:02d}", "response_time": random.randint(100, 500),
    "status_code": random.choice([200, 400, 500]), "application": random.choice(["Desktop", "Mobile"]),
    "transaction": random.choice(["Login", "Checkout", "Add to Cart", "Logout"])}
    for i in range(60)
]
df_lr = pd.DataFrame(lr_data)


# Function to fetch and process data
def fetch_and_process_data(metric_ids, start_time, end_time, granularity):
    print(metric_ids)
    # selected_servers = "HOST-000553947E276A2C"
    
    # Get metrics data in CSV format
    # metrics_data = dt_client.get_metrics(
    #     selected_servers, metric_ids, start_time, end_time, granularity, response_format="csv"
    # )

    # Define the API endpoint
    base_url = "http://127.0.0.1:5000/metrics"  # Update if running on a different host
    
    # Set query parameters
    params = {
        "metricId": metric_ids,
        "from": start_time,
        "now": end_time,
        "granularity": granularity
    }

    # Send a GET request
    metrics_data = requests.get(base_url, params=params)
    # print (metrics_data.text)

    # Read CSV with proper headers
    df = pd.read_csv(StringIO(metrics_data.text), header=0)

    # Ensure expected columns exist
    expected_columns = ["metricId", "dt.entity.host", "time", "value"]
    if not all(col in df.columns for col in expected_columns):
        raise ValueError(f"Unexpected column names in CSV: {df.columns.tolist()}")

    # Convert 'time' column to datetime
    df["time"] = pd.to_datetime(df["time"], errors="coerce")

    # Convert 'value' column to numeric, dropping invalid values
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["value"])  # Drop missing values

    # 🔹 Pivot data to include both metric and server name
    df_pivot = df.pivot_table(
        index="time",
        columns=["metricId", "dt.entity.host"],  # Keep metric + host
        values="value",
        aggfunc="mean"
    )

    # 🔹 Flatten MultiIndex columns
    df_pivot.columns = [f"{metric} | {host}" for metric, host in df_pivot.columns]
    df_pivot = df_pivot.reset_index()  # Keep 'time' as a normal column

    return df_pivot


# Fetch all Test Set IDs
test_ids = fetch_all_test_ids()

# Fetch all test details dynamically
test_details_map = {test_id: fetch_test_details(test_id).get("testScenarioName", "Unknown") for test_id in test_ids}

# Generate dropdown options (Display: "ID - Scenario Name", Value: "ID")
test_options = {f"{test_id} - {scenario}": test_id for test_id, scenario in test_details_map.items()}

server_options = []

server_options_mock_dict = {
    "HOST-000553947E276A2C": "Server A",
    "HOST-123456789ABCDEF": "Server B"
}

# Page Configuration
st.set_page_config(layout="wide")
st.title("📊 Comprehensive Monitoring - Observability Dashboard")

# Layout Sections
col1, col2, col3 = st.columns([0.15, 0.7, 0.15], gap="medium")

with col1:
    st.header("Navigation")
    st.markdown("[Server Usage](#server-usage)")
    st.markdown("[LoadRunner Metrics](#loadrunner-metrics)")
    st.markdown("[Splunk Details](#splunk-details)")


applications_server = {
    "Mobile": ["Server1", "Server2"],
    "OOLB": ["Server3", "Server4", "Server5", "Server6", "Server7", "Server8", "Server9"]
}


# Function to get user-friendly name
def get_friendly_server_name(host_id):
    """Returns a user-friendly server name using dropdown mapping or REST API fallback."""
    print('host' + host_id)
    print(servers_dict)
    if host_id in servers_dict:
        return servers_dict[host_id]
    
    # REST API call to fetch the server name if not found
    response = requests.get(f"http://127.0.0.1:5000/get_server_name?host={host_id}")
    if response.status_code == 200:
        return response.json().get("friendly_name", host_id)
    
    return host_id  # Default fallback to original ID

def format_datetime_custom(dt, iso_format=False):
    """
    Formats datetime object to Dynatrace API-compatible string.
    
    Args:
        dt (datetime): The datetime object.
        iso_format (bool): If True, includes milliseconds and timezone offset.
    
    Returns:
        str: Formatted datetime string.
    """
    if iso_format:
        return dt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + "+00:00"
    return dt.strftime('%Y-%m-%dT%H:%M:%S')

def format_datetime(timestamp):
    """Ensure the timestamp is converted to 'YYYY-MM-DD HH:MM' format."""
    if isinstance(timestamp, str):
        try:
            # Try parsing with seconds
            timestamp = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            # If that fails, try parsing without seconds
            timestamp = datetime.strptime(timestamp, "%Y-%m-%d %H:%M")
    
    return timestamp.strftime("%Y-%m-%d %H:%M")

# --- Splunk API Call Function ---
def fetch_splunk_data(application, start_date, end_date, granularity, mode="mock"):

    # start_date = "2025-02-26 11:00:00"  # Assign a string in the correct format
    # end_date = "2025-03-23 11:00:00"
    """Fetch data from Splunk or mock files based on the mode."""
    start_time = format_datetime(start_date)
    end_time = format_datetime(end_date)

    # Dictionary to store results from data sources
    results = {}

    # Prepare request payload
    payload = {
        "application": application,
        "start_date": start_time,
        "end_date": end_time,
        "granularity": granularity
    }


    # Fetch queries associated with the application
    for query in APPLICATION_QUERIES.get(application, []):
        if mode == "real":
            results[query["name"]] = splunk.execute_query(query["query"])  # Fetch real Splunk data
        else:
            results[query["name"]] = splunk.read_mock_data(query["mock_file"], format_datetime(start_time), format_datetime(end_time))  # Read mock data
    
    # print(results)
    return results

#############DUMMY ANALYSIS###############################


# with col3:
#     st.header("📝 Observations")
#     # Perform Analysis
#     st.text_area("Here are our observations:", value="we will show analyzed data here", height=600, disabled=False)



with col2:

    # Initialize session state for button click
    if "fetch_data_clicked" not in st.session_state:
        st.session_state.fetch_data_clicked = False

    # Filter Section
    st.subheader("🔍 Filter Parameters")
    
    col_filter1, col_filter2, col_filter3, col_filter4, col_filter5 = st.columns([3,3,2,2,2])
    app_name = col_filter1.selectbox("Application Name", options=APPLICATIONS, key="app_name")

    # Dynamically update Test Set and Server Name based on Application selection
    # Generate dropdown options in "TestID - TestScenarioName" format
    test_options = {
        f"{scenario['testID']} - {scenario['testScenarioName']}": scenario['testID']
        for scenario in test_scenarios.get(app_name, [])
    }

        
    # Fetch the management zone name for the given application from the config file
    mz_name = config.get("applications", {}).get(app_name, {}).get("management_zone", "")

    # If no management zone is found, return an empty list
    if not mz_name:
        server_options = []
    else:
        # Fetch servers from Dynatrace API
        servers_dict = dt_client.get_hosts_by_management_zone(mz_name)
        
        # Extract only the display names of the servers
        server_options = list(servers_dict.values())

    # Debugging output (optional)
    print(f"Servers for {app_name} (MZ: {mz_name}): {server_options}")

    # Default start & end dates (1 day difference)
    default_start_date = datetime.now() - timedelta(days=1)
    default_end_date = datetime.now()

    # Initialize session state variables
    if "start_date" not in st.session_state:
        st.session_state.start_date = default_start_date
    if "end_date" not in st.session_state:
        st.session_state.end_date = default_end_date
    if "selected_test_id" not in st.session_state:
        st.session_state.selected_test_id = None
    if "selected_test_set" not in st.session_state:
        st.session_state.selected_test_set = None
    if "test_scenario_name" not in st.session_state:
        st.session_state.test_scenario_name = ""
    if "transaction_names" not in st.session_state:
        st.session_state.transaction_names = []

    test_set = col_filter2.selectbox("Test Set ID", options=test_options, key="test_set_dropdown")
    # Extract only the Test ID from the selection
    selected_test_id = test_options[test_set]
    
    print(selected_test_id)
    print(st.session_state.selected_test_id)
    # If test set changes, reset transactions & dates
    if selected_test_id != st.session_state.selected_test_id:
        st.session_state.transaction_names = []
        st.session_state.selected_transaction = None
        st.session_state.start_date = default_start_date
        st.session_state.end_date = default_end_date

    # Button to fetch details
    with col_filter5:
        st.markdown("<br>", unsafe_allow_html=True)  # For vertical alignment
        if st.button("Fetch Test Details"):
            st.session_state.selected_test_id = selected_test_id  # Store Test Set ID
            test_details = fetch_test_details(st.session_state.selected_test_id)
            print(test_details)

            if test_details:
                st.session_state.start_date = datetime.strptime(test_details["start_date"], "%Y-%m-%d")
                st.session_state.end_date = datetime.strptime(test_details["end_date"], "%Y-%m-%d")
                st.session_state.test_scenario_name = test_details["testScenarioName"]

            st.session_state.transaction_names = fetch_transactions_for_test(st.session_state.selected_test_id)
    
    # Date Inputs
    # With these updated lines:
    start_date = col_filter3.date_input("Start Date", value=st.session_state.start_date, key="start_date_picker")
    end_date = col_filter4.date_input("End Date", value=st.session_state.end_date, key="end_date_picker")


    col_filter5, col_filter6, col_filter7, col_filter8 = st.columns(4)
    granularity = col_filter5.selectbox("Granularity", options=["1m", "5m", "15m", "1h"], key="granularity")
    
    # Update transaction names based on selected Test Set
    transaction_name = col_filter6.selectbox("Transaction Name", st.session_state.transaction_names)


    server_name = col_filter7.multiselect("Server Name", options=server_options, key="server_name_dropdown")
    
    col_space ,col_button1, col_button2,  col_button3,  col_space = st.columns([2,1,1,1, 2])
    with col_button1:
        if st.button("Fetch Data"):
            st.session_state.fetch_data_clicked = True
            # message = st.success("Fetching data...")
            # time.sleep(2)  # Wait for 2 seconds
            # message.empty()  # Clear the success message
            # st.toast("Processing complete!", icon="✅")  # Alert-like notification
            
    with col_button2:
        if st.button("Reset Filters"):
            st.session_state.fetch_data_clicked = False

    
    with col_button3:
        if st.button("Save Snapshot"):
            st.session_state.fetch_data_clicked = False
    

    
    # Only fetch and display data if the button was clicked

    if st.session_state.fetch_data_clicked:
        # KPI Metrics Section
        st.subheader("📈 Performance Overview")

        # Create three columns to display key performance indicators (KPIs)
        col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
        col_kpi1.metric("Average CPU Utilization", "45%")
        col_kpi2.metric("Average Memory Utilization", "60%")
        col_kpi3.metric("Total Errors", "12")

        # Generate a time series for plotting data
        time_series = pd.date_range(start=start_date, end=end_date, freq="1H")

        # Get the list of servers for the selected application
        selected_servers = applications_server.get(app_name, [])

        # Dynatrace Metrics Section
        st.subheader("📊 Dynatrace Metrics")

        # Convert dates to Unix timestamp (milliseconds) for Dynatrace
        # Convert to string in YYYY-MM-DD format if they are datetime objects
        if isinstance(start_date, str):
            start_date_str = start_date  # Already a string
        else:
            start_date_str = start_date.strftime("%Y-%m-%d") if start_date else None

        if isinstance(end_date, str):
            end_date_str = end_date  # Already a string
        else:
            end_date_str = end_date.strftime("%Y-%m-%d") if end_date else None

        # Convert dates to Unix timestamp (milliseconds) for Dynatrace
        try:
            start_ts = int(time.mktime(time.strptime(start_date_str, "%Y-%m-%d"))) * 1000 if start_date_str else None
            end_ts = int(time.mktime(time.strptime(end_date_str, "%Y-%m-%d"))) * 1000 if end_date_str else None
        except Exception as e:
            st.error(f"Error converting dates: {e}")
            start_ts, end_ts = None, None  # Fallback to None if conversion fails


        # Fetch the dashboard URL and replace timestamps
        #dashboard_url_template = config["applications"][app_name]["dashboard_url_template"]
        dashboard_url_template = config["applications"][app_name].get("dashboard_url_template")
        if dashboard_url_template:
            dashboard_url = dashboard_url_template.replace("{from_ts}", str(start_ts)).replace("{to_ts}", str(end_ts))
        else:
            dashboard_url = "#"


        colblank, col1 = st.columns([4,1])
        #show hyper link
        # Read hyperlink from config
        
        with col1:
            st.markdown(
                f"""
                <div style="text-align: right;">
                    <a href="{dashboard_url}" target="_blank" style="text-decoration: none; font-size: 16px;">
                        🔗 More Details
                    </a>
                </div>
                """,
                unsafe_allow_html=True
            )

        # Load default metrics and application-specific metrics from configuration
        default_metrics = config.get("default_metrics", [])
        application_metrics = config.get("applications", {}).get(app_name, {}).get("metrics", [])

        # Combine both metric lists into a single list
        metric_ids = [metric["id"] for metric in default_metrics + application_metrics]
        metric_labels = {metric["id"]: metric["label"] for metric in default_metrics + application_metrics}

        # Fetch and process metric data
        df_list = []  # List to store dataframes
        valid_metric_ids = []  # Track valid metrics

        for metric_id in metric_ids:
            # Fetch data for each metric separately
            df = fetch_and_process_data([metric_id], format_datetime_custom(start_date), format_datetime_custom(end_date), granularity)

            if not df.empty:  # If data exists, add it to the list
                df_list.append(df)
                valid_metric_ids.append(metric_id)  # Track valid metric
            else:
                # Create an empty DataFrame as a placeholder for missing data
                df_empty = pd.DataFrame({"time": pd.date_range(start=start_date, end=end_date, freq="5min")})
                df_empty[metric_id] = None  # Fill metric column with NaN (ensures blank graph)
                df_list.append(df_empty)
                valid_metric_ids.append(metric_id)  # Still track the metric for plotting

        # Ensure there's at least one valid dataframe before merging
        if df_list:
            # Merge all dataframes on the "time" column, ensuring proper alignment
            df_pivot = pd.concat(df_list, axis=1).reset_index()

            # Drop extra "index" column if present
            if "index" in df_pivot.columns:
                df_pivot = df_pivot.drop(columns=["index"])

            # Drop duplicate "time" columns, keeping only one
            df_pivot = df_pivot.loc[:, ~df_pivot.columns.duplicated()]

            # Ensure 'time' is in datetime format
            df_pivot["time"] = pd.to_datetime(df_pivot["time"], errors="coerce")

            # Create a two-column layout for displaying plots
            col1, col2 = st.columns(2)

            # st.write("### Debug: Dataset Used for Analysis & Plotting")
            # st.dataframe(df_pivot)
            
            # Loop through each valid metric and generate plots
            for i, metric_id in enumerate(valid_metric_ids):  
                # Find all matching columns (i.e., metrics recorded for different servers)
                matching_columns = [col for col in df_pivot.columns if metric_id in col]

                if matching_columns:
                    # Extract server names from column names
                    server_names = {col: get_friendly_server_name(col.split(" | ")[-1]) for col in matching_columns}

                    # Rename columns to display only server names
                    df_display = df_pivot.rename(columns=server_names)

                    # Determine the maximum Y value in the dataset
                    y_max = df_display[list(server_names.values())].max().max()

                    # Calculate the total time range in hours
                    time_range_hours = (df_display["time"].max() - df_display["time"].min()).total_seconds() / 3600

                    # Dynamically set the tick interval based on the time range
                    if time_range_hours <= 6:
                        tick_interval = 3600000  # 1 hour
                    elif time_range_hours <= 24:
                        tick_interval = 10800000  # 3 hours
                    elif time_range_hours <= 72:
                        tick_interval = 21600000  # 6 hours
                    else:
                        tick_interval = 43200000  # 12 hours

                    # Create the line plot using Plotly
                    fig = px.line(df_display, x="time", y=list(server_names.values()),
                                labels={"value": metric_labels[metric_id], "variable": "Server"},
                                title=metric_labels[metric_id], color_discrete_sequence=px.colors.qualitative.Set1,
                                line_shape="linear")  # Ensures smooth connection

                    # Update layout with dynamic Y-axis limit
                    fig.update_layout(yaxis=dict(range=[0, get_y_axis_limit(y_max)]))

                    # Ensure missing data points are connected
                    fig.update_traces(connectgaps=True)

                    # Function to customize time labels dynamically
                    def custom_time_labels(timestamps):
                        labels = []
                        for t in timestamps:
                            # Show full date format at midnight, otherwise show just time
                            if t.hour == 0 and t.minute == 0:
                                labels.append(t.strftime("%d-%m %H:%M"))
                            else:
                                labels.append(t.strftime("%H:%M"))
                        return labels

                    # Generate tick values dynamically based on the time range
                    if time_range_hours <= 6:
                        tick_interval = "1H"
                    elif time_range_hours <= 24:
                        tick_interval = "3H"
                    elif time_range_hours <= 72:
                        tick_interval = "6H"
                    else:
                        tick_interval = "12H"

                    # Create tick values for x-axis
                    tick_values = pd.date_range(df_display["time"].min(), df_display["time"].max(), freq=tick_interval)
                    tick_labels = custom_time_labels(tick_values)  # Format labels

                    # Update x-axis with custom tick labels
                    fig.update_layout(
                        xaxis=dict(
                            tickvals=tick_values,
                            ticktext=tick_labels
                        )
                    )

                    # Alternate between two columns for better visual balance
                    col = col1 if i % 2 == 0 else col2
                    with col:
                        st.plotly_chart(fig, use_container_width=True)

        else:
            # Show an error message if no valid data is available
            st.error("No valid data available for any metrics.")


    # if st.session_state.fetch_data_clicked:
    #     # KPI Metrics Section
    #     st.subheader("📈 Performance Overview")
    #     col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    #     col_kpi1.metric("Average CPU Utilization", "45%")
    #     col_kpi2.metric("Average Memory Utilization", "60%")
    #     col_kpi3.metric("Total Errors", "12")
        
    #     # Generate CPU, Memory, and GC data
    #     time_series = pd.date_range(start=start_date, end=end_date, freq="1H")
        
    #     selected_servers = applications_server.get(app_name, [])

    #     # Dynatrace Section
    #     st.subheader("📊 Dynatrace Metrics")

    #     # Load default and application-specific metrics
    #     default_metrics = config.get("default_metrics", [])
    #     application_metrics = config.get("applications", {}).get(app_name, {}).get("metrics", [])

    #     # Combine default and application-specific metrics
    #     metric_ids = [metric["id"] for metric in default_metrics + application_metrics]
    #     metric_labels = {metric["id"]: metric["label"] for metric in default_metrics + application_metrics}

    #     # print(default_metrics)
    #     # Fetch and process metric data

    #     # Fetch data for each metric ID separately and combine results
    #     df_list = []
    #     valid_metric_ids = []  # Keep track of valid metrics

    #     for metric_id in metric_ids:
    #         #df = fetch_and_process_data([metric_id], start_date, end_date)  # Pass one metric at a time
    #         df = fetch_and_process_data([metric_id], format_datetime_custom(start_date), format_datetime_custom(end_date), granularity)
            
    #         if not df.empty:  # Only append if data exists
    #             df_list.append(df)
    #             valid_metric_ids.append(metric_id)  # Track valid metric
    #         else:
    #             # Create an empty DataFrame with time range to show as a placeholder
    #             df_empty = pd.DataFrame({"time": pd.date_range(start=start_date, end=end_date, freq="5min")})
    #             df_empty[metric_id] = None  # Fill metric column with NaN (ensures blank graph)
    #             df_list.append(df_empty)
    #             valid_metric_ids.append(metric_id)  # Still track this metric for plotting

        
    #     # Ensure we have at least one valid dataframe before merging
    #     if df_list:
    #         # Merge all dataframes on the "time" column, ignoring completely missing ones
    #         df_pivot = pd.concat(df_list, axis=1).reset_index()

    #         # Drop extra "index" column if present
    #         if "index" in df_pivot.columns:
    #             df_pivot = df_pivot.drop(columns=["index"])

    #         # Drop duplicate "time" columns, keeping only one
    #         df_pivot = df_pivot.loc[:, ~df_pivot.columns.duplicated()]

    #         # Ensure 'time' is in datetime format
    #         df_pivot["time"] = pd.to_datetime(df_pivot["time"], errors="coerce")

    #         # Create two columns layout
    #         col1, col2 = st.columns(2)

    #         # Loop through each valid metric and plot it
    #         for i, metric_id in enumerate(valid_metric_ids):  # Use `valid_metric_ids` to avoid missing ones
    #             # Find all matching columns (metrics for different hosts)
    #             matching_columns = [col for col in df_pivot.columns if metric_id in col]

    #             if matching_columns:
    #                 # Extract server IDs from column names
    #                 server_names = {col: get_friendly_server_name(col.split(" | ")[-1]) for col in matching_columns}

    #                 # Rename columns to show only server names
    #                 df_display = df_pivot.rename(columns=server_names)

    #                 # Determine max Y value from the dataset
    #                 y_max = df_display[list(server_names.values())].max().max()  # Find highest Y value

    #                 # Calculate time range in hours
    #                 time_range_hours = (df_display["time"].max() - df_display["time"].min()).total_seconds() / 3600

    #                 # Determine suitable tick interval
    #                 if time_range_hours <= 6:
    #                     tick_interval = 3600000  # 1 hour
    #                 elif time_range_hours <= 24:
    #                     tick_interval = 10800000  # 3 hours
    #                 elif time_range_hours <= 72:
    #                     tick_interval = 21600000  # 6 hours
    #                 else:
    #                     tick_interval = 43200000  # 12 hours

                    

    #                 # Create the line plot
    #                 fig = px.line(df_display, x="time", y=list(server_names.values()),
    #                             labels={"value": metric_labels[metric_id], "variable": "Server"},
    #                             title=metric_labels[metric_id], color_discrete_sequence=px.colors.qualitative.Set1,
    #                             line_shape="linear")  # Ensures smooth connection
                    
    #                 # Update layout with dynamic Y-axis
    #                 fig.update_layout(yaxis=dict(range=[0, get_y_axis_limit(y_max)]))

    #                 # Connect missing data points
    #                 fig.update_traces(connectgaps=True)

                    
    #                 # Function to format time labels dynamically
    #                 def custom_time_labels(timestamps):
    #                     labels = []
    #                     for t in timestamps:
    #                         if t.hour == 0 and t.minute == 0:  # Midnight case
    #                             labels.append(t.strftime("%d-%m %H:%M"))
    #                         else:  # Regular case
    #                             labels.append(t.strftime("%H:%M"))
    #                     return labels
                    
    #                 # Generate tick values (e.g., every hour based on dynamic interval)
    #                 time_range_hours = (df_display["time"].max() - df_display["time"].min()).total_seconds() / 3600

    #                 if time_range_hours <= 6:
    #                     tick_interval = "1H"
    #                 elif time_range_hours <= 24:
    #                     tick_interval = "3H"
    #                 elif time_range_hours <= 72:
    #                     tick_interval = "6H"
    #                 else:
    #                     tick_interval = "12H"

    #                 # Convert time column to list and generate formatted labels
    #                 tick_values = pd.date_range(df_display["time"].min(), df_display["time"].max(), freq=tick_interval)
    #                 tick_labels = custom_time_labels(tick_values)

    #                 # Update x-axis with custom tick labels
    #                 fig.update_layout(
    #                     xaxis=dict(
    #                         tickvals=tick_values,
    #                         ticktext=tick_labels
    #                     )
    #                 )

    #                 # Alternate between columns
    #                 col = col1 if i % 2 == 0 else col2
    #                 with col:
    #                     st.plotly_chart(fig, use_container_width=True)

    #     else:
    #         st.error("No valid data available for any metrics.")


        # LoadRunner Section
        st.subheader("📊 LoadRunner Metrics")

        col1, col2 = st.columns(2)
        # Transaction Response Time Line Chart
        fig_response = px.line(df_lr, x='timestamp', y='response_time', title="Transaction Response Time")
        col1.plotly_chart(fig_response, use_container_width=True)

        # TPS Over Time Line Chart
        fig_tps = px.line(df_lr, x='timestamp', y='response_time', color='transaction', title="TPS Over Time")
        col2.plotly_chart(fig_tps, use_container_width=True)

        col1, col2 = st.columns(2)
        # HTTP Status Code Pie Chart
        fig_pie = px.pie(df_lr, names='status_code', title="HTTP Status Codes")
        col1.plotly_chart(fig_pie, use_container_width=True)

        # Server Hits Pie Chart
        fig_server = px.pie(df_lr, names='application', title="Server Hits", hole=0.4)
        col2.plotly_chart(fig_server, use_container_width=True)

        st.dataframe(generate_transaction_data_lr(), use_container_width=True)
        
        # Splunk Section
        st.subheader("📂 Splunk Data Logs")

        # Store application-specific Splunk queries
        APPLICATION_QUERIES = {
            app: details.get("splunk_queries", []) for app, details in config["applications"].items()
        }

        data = fetch_splunk_data(
            application=app_name,
            start_date=start_date,
            end_date=end_date,
            granularity=granularity,
            mode="mock"
        )

        if "error" in data:
            st.error(f"❌ Error: {data['error']}")
        else:
            st.subheader(f"📌 Splunk Data for {app_name}")

            for query_name, records in data.items():
                # df = pd.DataFrame(records)
                df = pd.DataFrame(records) if isinstance(records, list) and len(records) > 0 else pd.DataFrame(columns=["No Data"])

                if df.empty:
                    st.warning(f"No data found for {query_name}")
                    continue

                st.markdown(f"### {query_name} ({len(df)} records)")

                # Configure AgGrid
                gb = GridOptionsBuilder.from_dataframe(df)
                gb.configure_pagination(enabled=True, paginationAutoPageSize=False, paginationPageSize=15)  # 15 rows per page
                gb.configure_side_bar()  # Enable sidebar for column selection
                gb.configure_default_column(editable=False, groupable=True, filter=True, resizable=True, sortable=True)
                gb.configure_grid_options(domLayout='autoHeight')  # Ensures full-screen view

                grid_options = gb.build()

                # Display AgGrid with full-screen option
                grid_response = AgGrid(df, gridOptions=grid_options, height=600, fit_columns_on_grid_load=True)

                # Download Button
                csv_data = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download CSV",
                    data=csv_data,
                    file_name=f"{query_name}_splunk_data.csv",
                    mime="text/csv"
                )
    st.session_state.fetch_data_clicked = False    


# with col3:
#     st.header("📝 Observations")

#     if not df_pivot.empty:
#         # Ensure 'time' column is in datetime format
#         df_pivot["time"] = pd.to_datetime(df_pivot["time"])

#         # Identify CPU columns explicitly
#         cpu_columns = [col for col in df_pivot.columns if "cpu.usage" in col]

#         # Find maximum CPU usage for each timestamp
#         df_pivot["max_cpu_usage"] = df_pivot[cpu_columns].max(axis=1)

#         # Get the top 4 highest spikes
#         top_spikes = df_pivot.nlargest(4, "max_cpu_usage")

#         # Extract timestamps of top spikes
#         spike_times = top_spikes["time"].dt.strftime("%d-%m %H:%M").tolist()
#         spike_values = top_spikes["max_cpu_usage"].tolist()

#         # Generate Observations
#         observations = "🔹 **Top 4 CPU Spikes:**\n"
#         for i in range(len(spike_times)):
#             observations += f"   - 📍 **{spike_times[i]}** → {spike_values[i]:.2f}% CPU\n"

#         st.text_area("Here are our observations:", value=observations, height=200, disabled=True)

#     else:
#         st.text_area("Here are our observations:", value="No data available for analysis.", height=400, disabled=True)


with col3:
    st.header("📝 System Observations")

    if not df_pivot.empty:
        # Ensure 'time' column is in datetime format
        df_pivot["time"] = pd.to_datetime(df_pivot["time"])

        # Identify CPU columns explicitly
        cpu_columns = [col for col in df_pivot.columns if "cpu.usage" in col]
        memory_column = [col for col in df_pivot.columns if "builtin:host.mem.usage" in col]

        # Compute Max CPU Usage per timestamp
        df_pivot["max_cpu_usage"] = df_pivot[cpu_columns].max(axis=1) if cpu_columns else None

        # Compute average CPU utilization on the full dataset (excluding NaN values)
        avg_cpu = df_pivot["max_cpu_usage"].dropna().mean() if cpu_columns else None

        # Get the top 50 highest CPU spikes
        if cpu_columns:
            top_50_cpu_spikes = df_pivot.nlargest(50, "max_cpu_usage")
            top_50_cpu_spikes = top_50_cpu_spikes.sort_values(by="time")

            # Filter spikes that occur at least 5 minutes apart
            selected_cpu_spikes = []
            last_selected_time = None
            for _, row in top_50_cpu_spikes.iterrows():
                current_time = row["time"]
                if last_selected_time is None or (current_time - last_selected_time).total_seconds() > 300:
                    selected_cpu_spikes.append(row)
                    last_selected_time = current_time

            # Convert list to DataFrame
            filtered_cpu_spikes = pd.DataFrame(selected_cpu_spikes)

            # Get only the top 5 CPU spikes
            top_final_cpu_spikes = filtered_cpu_spikes.nlargest(5, "max_cpu_usage")

            # Extract timestamps & values
            cpu_times = top_final_cpu_spikes["time"].dt.strftime("%d-%m %H:%M").tolist()
            cpu_values = top_final_cpu_spikes["max_cpu_usage"].tolist()
        else:
            cpu_times, cpu_values = [], []

        # --- Memory Spike Detection ---
        if memory_column:
            
            # Compute Max Memory Usage per timestamp (assuming multiple columns can exist)
            df_pivot["max_mem_usage"] = df_pivot[memory_column].max(axis=1)

            # Compute average Memory utilization on full dataset (excluding NaN values)
            avg_memory = df_pivot["max_mem_usage"].dropna().mean()

            # Get the top 50 highest Memory spikes
            memory_threshold = df_pivot["max_mem_usage"].quantile(0.95)
            memory_spikes = df_pivot[df_pivot["max_mem_usage"] > memory_threshold].dropna()
            memory_spikes = memory_spikes.nlargest(50, "max_mem_usage").sort_values(by="time")

            # Filter memory spikes that occur at least 5 minutes apart
            selected_memory_spikes = []
            last_selected_time = None
            for _, row in memory_spikes.iterrows():
                current_time = row["time"]
                if last_selected_time is None or (current_time - last_selected_time).total_seconds() > 300:
                    selected_memory_spikes.append(row)
                    last_selected_time = current_time

            # Convert list to DataFrame
            filtered_memory_spikes = pd.DataFrame(selected_memory_spikes)

            # Get only the top 5 memory spikes
            top_final_memory_spikes = filtered_memory_spikes.nlargest(5, "max_mem_usage")

            # Extract timestamps & values
            mem_times = top_final_memory_spikes["time"].dt.strftime("%d-%m %H:%M").tolist()
            mem_values = top_final_memory_spikes["max_mem_usage"].tolist()
        else:
            mem_times, mem_values = [], []

        # Generate Observations
        observations = "📊 **System Utilization Summary:**\n"

        # Include average CPU & Memory utilization in summary
        observations += f"   - 🖥 **Average CPU Utilization:** {avg_cpu:.2f}%\n" if avg_cpu is not None else "   - 🖥 **Average CPU Utilization:** N/A\n"
        observations += f"   - 🗂 **Average Memory Utilization:** {avg_memory:.2f}%\n\n" if avg_memory is not None else "   - 🗂 **Average Memory Utilization:** N/A\n\n"


        # Include CPU utilization in summary
        if cpu_times:
            observations += "🔹 **Top 5 Major CPU Spikes Detected:**\n"
            for i in range(len(cpu_times)):
                observations += f"   - 📍 **{cpu_times[i]}** → {cpu_values[i]:.2f}% CPU\n"
        else:
            observations += "🔹 **No Major CPU Spikes Detected.**\n"

        # Include Memory utilization in summary
        if mem_times:
            observations += "\n🔹 **Top 5 Major Memory Spikes Detected:**\n"
            for i in range(len(mem_times)):
                observations += f"   - 📍 **{mem_times[i]}** → {mem_values[i]:.2f}% Memory\n"
        else:
            observations += "\n🔹 **No Major Memory Spikes Detected.**\n"

        # Show summary metrics
        # st.metric(label="Total Major CPU Spikes", value=len(cpu_times) if cpu_times else "N/A")
        # st.metric(label="Total Major Memory Spikes", value=len(mem_times) if mem_times else "N/A")
        st.text_area("Here are observations:", value=observations, height=600, disabled=False)

    else:
        st.text_area("Here are observations:", value="No data available for analysis.", height=300, disabled=True)
