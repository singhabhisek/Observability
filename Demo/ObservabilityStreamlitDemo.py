from io import StringIO
import streamlit as st
import pandas as pd
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



# Function to fetch and process data
def fetch_and_process_data(metric_ids, start_time, end_time):
    selected_servers = "HOST-000553947E276A2C"
    
    # Get metrics data in CSV format
    metrics_data = dt_client.get_metrics(
        selected_servers, metric_ids, start_time, end_time, granularity, response_format="csv"
    )

    # Read CSV with proper headers
    df = pd.read_csv(StringIO(metrics_data), header=0)

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

# Simulated API response (CSV format)
csv_data = """metricId,dt.entity.host,time,value
builtin:host.cpu.usage,HOST-000553947E276A2C,2025-03-10 10:45:00,6.48
builtin:host.cpu.usage,HOST-000553947E276A2C,2025-03-10 10:46:00,9.74
builtin:host.cpu.usage,HOST-000553947E276A2C,2025-03-10 10:47:00,8.41
builtin:host.cpu.usage,HOST-000553947E276A2C,2025-03-10 10:48:00,9.71
builtin:host.cpu.usage,HOST-000553947E276A2C,2025-03-10 10:49:00,10.68
builtin:host.cpu.usage,HOST-000553947E276A2C,2025-03-10 10:50:00,7.85
builtin:host.cpu.usage,HOST-000553947E276A2C,2025-03-10 10:51:00,7.24
builtin:host.cpu.usage,HOST-000553947E276A2C,2025-03-10 10:52:00,7.81
builtin:host.cpu.usage,HOST-000553947E276A2C,2025-03-10 10:53:00,11.13
builtin:host.cpu.usage,HOST-123456789ABCDEF,2025-03-10 10:45:00,6.48
builtin:host.cpu.usage,HOST-123456789ABCDEF,2025-03-10 10:46:00,6.20
builtin:host.cpu.usage,HOST-123456789ABCDEF,2025-03-10 10:47:00,7.55
builtin:host.cpu.usage,HOST-123456789ABCDEF,2025-03-10 10:48:00,8.30
builtin:host.cpu.usage,HOST-123456789ABCDEF,2025-03-10 10:49:00,7.85
builtin:host.cpu.usage,HOST-123456789ABCDEF,2025-03-10 10:50:00,9.20
"""

# Load CSV into Pandas DataFrame
df_dt = pd.read_csv(StringIO(csv_data))

# Convert time column to datetime
df_dt["time"] = pd.to_datetime(df_dt["time"])



# Fetch all Test Set IDs
test_ids = fetch_all_test_ids()

# Fetch all test details dynamically
test_details_map = {test_id: fetch_test_details(test_id).get("testScenarioName", "Unknown") for test_id in test_ids}

# Generate dropdown options (Display: "ID - Scenario Name", Value: "ID")
test_options = {f"{test_id} - {scenario}": test_id for test_id, scenario in test_details_map.items()}


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

# Function to generate dummy transaction data
def generate_transaction_data():
    return pd.DataFrame({
        "Time": pd.date_range(start="2024-03-01", periods=50, freq="T"),  # Time-based data
        "CPU Server1": [random.uniform(30, 95) for _ in range(50)], 
        "Memory Server1": [random.uniform(80, 98) for _ in range(50)],
        "CPU Server2": [random.uniform(20, 90) for _ in range(50)],
        "Memory Server2": [random.uniform(30, 95) for _ in range(50)]
    })


# Generate Data
df = generate_transaction_data()

# Function to analyze high CPU/Memory utilization
def analyze_data(df):
    analysis = []
    
    for col in df.columns:
        if "CPU" in col or "Memory" in col:
            high_utilization = df[df[col] > 80]  # Filter where utilization > 80%
            high_count = len(high_utilization)
            avg_utilization = df[col].mean()
            
            if high_count > 0:
                duration = (high_utilization["Time"].max() - high_utilization["Time"].min()).seconds / 60
                analysis.append(f"🔴 **{col} exceeded 80% utilization {high_count} times.** Total duration: {duration:.2f} min.")
            
            analysis.append(f"⚡ **Average {col} utilization:** {avg_utilization:.2f}%")
    
    if not analysis:
        analysis.append("✅ No anomalies detected in CPU or Memory utilization.")
    
    return analysis



with col3:
    st.header("📝 Observations")
    
    # Perform Analysis
    analysis_results = analyze_data(df)
    # Convert list of observations to a formatted string
    observations_text = "\n".join(f"- {result}" for result in analysis_results)

    # for result in analysis_results:
    #     st.markdown(f"- {result}")  # Display as bullet points
    st.text_area("Here are our observations:", value=observations_text, height=600, disabled=False)



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


    # server_options = applications_server.get(app_name, [])

    # replace the above line with this logic for Dynatrace
        
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
    
    col_space ,col_button1, col_button2, col_space = st.columns([2,1,1,2])
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
    

    
    # Only fetch and display data if the button was clicked
    if st.session_state.fetch_data_clicked:
        # KPI Metrics Section
        st.subheader("📈 Performance Overview")
        col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
        col_kpi1.metric("Average CPU Utilization", "45%")
        col_kpi2.metric("Average Memory Utilization", "60%")
        col_kpi3.metric("Total Errors", "12")
        
        # Generate CPU, Memory, and GC data
        time_series = pd.date_range(start=start_date, end=end_date, freq="1H")
        
        selected_servers = applications_server.get(app_name, [])

        # Generate Dummy Data
        lr_data = [
            {"timestamp": f"2025-03-03 12:{i:02d}", "response_time": random.randint(100, 500),
            "status_code": random.choice([200, 400, 500]), "application": random.choice(["Desktop", "Mobile"]),
            "transaction": random.choice(["Login", "Checkout", "Add to Cart", "Logout"])}
            for i in range(60)
        ]
        df_lr = pd.DataFrame(lr_data)

        data = {"Time": time_series}
        for server in selected_servers:
            data[f"CPU {server}"] = [random.uniform(20, 80) for _ in time_series]
            data[f"Memory {server}"] = [random.uniform(40, 90) for _ in time_series]
            data[f"GC {server}"] = [random.uniform(1, 10) for _ in time_series]

        df = pd.DataFrame(data)

        st.write(server_name)
        if server_name:
            
            cpu_columns = [f"CPU {s}" for s in server_name]
            memory_columns = [f"Memory {s}" for s in server_name]
            gc_columns = [f"GC {s}" for s in server_name]
            

            # Create CPU Usage Graph
            if cpu_columns:
                fig_cpu = px.line(df, x="Time", y=cpu_columns, 
                                title="CPU Usage Over Time", labels={"value": "CPU Usage (%)", "variable": "Server"},
                                template="plotly_dark")
                fig_cpu.update_layout(xaxis_title="Time", yaxis_title="CPU Usage (%)", hovermode="x unified")

            # Create Memory Usage Graph
            if memory_columns:
                fig_memory = px.line(df, x="Time", y=memory_columns, 
                                    title="Memory Usage Over Time", labels={"value": "Memory Usage (%)", "variable": "Server"},
                                    template="plotly_dark")
                fig_memory.update_layout(xaxis_title="Time", yaxis_title="Memory Usage (%)", hovermode="x unified")

            # Create Garbage Collection Graph
            if gc_columns:
                fig_gc = px.line(df, x="Time", y=gc_columns, 
                                title="Garbage Collection Over Time", labels={"value": "GC Events", "variable": "Server"},
                                template="plotly_dark")
                fig_gc.update_layout(xaxis_title="Time", yaxis_title="GC Events", hovermode="x unified")


        else:
            # Plot CPU Usage Graph
            fig_cpu = px.line(df, x="Time", y=[f"CPU {s}" for s in selected_servers], 
                            title="CPU Usage Over Time", labels={"value": "CPU Usage (%)", "variable": "Server"},
                            template="plotly_dark")
            fig_cpu.update_layout(xaxis_title="Time", yaxis_title="CPU Usage (%)", hovermode="x unified")

            # Plot Memory Usage Graph
            fig_memory = px.line(df, x="Time", y=[f"Memory {s}" for s in selected_servers], 
                                title="Memory Usage Over Time", labels={"value": "Memory Usage (%)", "variable": "Server"},
                                template="plotly_dark")
            fig_memory.update_layout(xaxis_title="Time", yaxis_title="Memory Usage (%)", hovermode="x unified")

            # Plot Garbage Collection Graph
            fig_gc = px.line(df, x="Time", y=[f"GC {s}" for s in selected_servers], 
                            title="Garbage Collection Over Time", labels={"value": "GC Events", "variable": "Server"},
                            template="plotly_dark")
            fig_gc.update_layout(xaxis_title="Time", yaxis_title="GC Events", hovermode="x unified")

        
        # Anotehr way to plot graphs - 
        # If no server selected, show data for all servers
        # if server_name:
        #     filtered_df = df_dt[df_dt["dt.entity.host"].isin(server_name)]
        # else:
        #     filtered_df = df_dt  # Show all servers

        # # Pivot Data for Plotly (Each Server as a Separate Column)
        # pivot_df = filtered_df.pivot(index="time", columns="dt.entity.host", values="value").reset_index()

        # # Ensure filtered data is not empty before plotting
        # if pivot_df.empty:
        #     st.warning("No data available for the selected server(s).")
        # else:
        #     fig = px.line(
        #         pivot_df,
        #         x="time",
        #         y=pivot_df.columns[1:],  # Select all server columns dynamically
        #         title="CPU Usage Over Time",
        #         labels={"value": "CPU Usage (%)", "time": "Timestamp", "dt.entity.host": "Server"},
        #         markers=True,
        #     )


        #invove rest apis  - 
        df_pivot = fetch_and_process_data('builtin:host.mem.usage','2025-03-08T01:00:00', '2025-03-09T02:00:00')
        # Plotly figure
        fig = px.line(
            df_pivot,
            x="time",  # X-axis: Time
            y=df_pivot.columns[1:],  # Y-axis: All metric columns (skip 'time')
            labels={"value": "Metric Value", "time": "Timestamp"},
            title="Server Metrics Over Time"
        )

        
        # Display the graphs with zoom and export options
        st.subheader("📊 Server Performance Metrics")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.plotly_chart(fig_cpu, use_container_width=True)
            st.download_button("Download CPU Data", df.to_csv(index=False), file_name="cpu_data.csv")

        with col2:
            st.plotly_chart(fig_memory, use_container_width=True)
            st.download_button("Download Memory Data", df.to_csv(index=False), file_name="memory_data.csv")

        with col3:
            st.plotly_chart(fig_gc, use_container_width=True)
            st.download_button("Download GC Data", df.to_csv(index=False), file_name="gc_data.csv")
        
        # 🎨 Plotly Express Line Chart
        def plot_metrics(df_pivot):
            # Reset index to make 'time' a column for Plotly
            df_pivot = df_pivot.reset_index()

            # ✅ Rename columns to extract only the hostname
            new_columns = {col: col.split("|")[-1].strip() for col in df_pivot.columns if col != "time"}
            df_pivot.rename(columns=new_columns, inplace=True)

            # ✅ Plot without melting
            fig = px.line(df_pivot, x='time', y=df_pivot.columns[1:], 
                        title="Metric Trends", labels={'value': 'Metric Value'},
                        markers=True)

            fig.update_layout(
                legend_title_text="Hostname",  # ✅ Legend will only show hostnames
                xaxis_title="Time",
                yaxis_title="Metric Value",
                hovermode="x"
            )

            return fig
        
        with col4:
            st.plotly_chart(plot_metrics(df_pivot), use_container_width=True)  # Ensure correct DataFrame is used

            # 🔹 Use df_pivot for downloading, since it contains processed data
            st.download_button(
                "Download CPU Data",
                df_pivot.to_csv(index=False),
                file_name="cpu_data.csv",
                mime="text/csv"
            )
            
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
                df = pd.DataFrame(records)

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


