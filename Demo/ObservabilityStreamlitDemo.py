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

splunk = SplunkAPI("test.com","abcd","def")


# Load Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
STATIC_FOLDER = os.path.join(BASE_DIR, "static")

with open(CONFIG_PATH, "r") as config_file:
    config = json.load(config_file)

APPLICATIONS = list(config.get("applications", {}).keys())

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

# Generate dummy transaction data
def generate_transaction_data():
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
    # Filter Section
    st.subheader("🔍 Filter Parameters")
    
    col_filter1, col_filter2, col_filter3, col_filter4 = st.columns(4)
    app_name = col_filter1.selectbox("Application Name", options=APPLICATIONS, key="app_name")

    # Dynamically update Test Set and Server Name based on Application selection
    # test_set_options = [t["testID"] for t in test_scenarios.get(app_name, [])]
    # Generate dropdown options in "TestID - TestScenarioName" format
    # Generate dropdown options in "TestID - TestScenarioName" format
    test_options = {
        f"{scenario['testID']} - {scenario['testScenarioName']}": scenario['testID']
        for scenario in test_scenarios.get(app_name, [])
    }


    server_options = applications_server.get(app_name, [])

    test_set = col_filter2.selectbox("Test Set ID", options=test_options, key="test_set_dropdown")
    # Extract only the Test ID from the selection
    selected_test_id = test_options[test_set]
    start_date = col_filter3.date_input("Start Date", value=datetime.now() - timedelta(days=1))
    end_date = col_filter4.date_input("End Date", value=datetime.now())
    
    col_filter5, col_filter6, col_filter7 = st.columns(3)
    granularity = col_filter5.selectbox("Granularity", options=["1m", "5m", "15m", "1h"], key="granularity")
    
    # Update transaction names based on selected Test Set
    # transaction_names = [t["testScenarioName"] for t in test_scenarios.get(app_name, []) if t["testID"] == test_set]
    # transaction_name = col_filter6.selectbox("Transaction Name", options=transaction_names, key="transaction_name_dropdown")
    transaction_options = transaction_data.get(selected_test_id, [])
    transaction_name = col_filter6.selectbox("Transaction Name", options=transaction_options, key="transaction_name")



    server_name = col_filter7.multiselect("Server Name", options=server_options, key="server_name_dropdown")
    
    col_button1, col_button2 = st.columns(2)
    with col_button1:
        if st.button("Fetch Data"):
            message = st.success("Fetching data...")
            time.sleep(2)  # Wait for 2 seconds
            message.empty()  # Clear the success message
            st.toast("Processing complete!", icon="✅")  # Alert-like notification
            
    with col_button2:
        if st.button("Reset Filters"):
            st.experimental_rerun()
    
    # KPI Metrics Section
    st.subheader("📈 Performance Overview")
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    col_kpi1.metric("Average CPU Utilization", "45%")
    col_kpi2.metric("Average Memory Utilization", "60%")
    col_kpi3.metric("Total Errors", "12")
    
    # Generate CPU, Memory, and GC data
    time_series = pd.date_range(start=start_date, end=end_date, freq="1H")


    # cpu_usage = [random.uniform(20, 80) for _ in time_series]
    # memory_usage = [random.uniform(40, 90) for _ in time_series]
    # gc_time = [random.uniform(1, 10) for _ in time_series]
    
    # usage_df = pd.DataFrame({"Time": time_series, "CPU Usage (%)": cpu_usage, "Memory Usage (%)": memory_usage, "Garbage Collection Time (ms)": gc_time})
    
    # # Dynatrace Server Usage Section
    # st.subheader("🖥️ Dynatrace Server Usage")
    # col_graph1, col_graph2, col_graph3 = st.columns(3)
    # with col_graph1:
    #     st.line_chart(usage_df.set_index("Time")["CPU Usage (%)"])
    # with col_graph2:
    #     st.line_chart(usage_df.set_index("Time")["Memory Usage (%)"])
    # with col_graph3:
    #     st.line_chart(usage_df.set_index("Time")["Garbage Collection Time (ms)"])
    
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

    # Display the graphs with zoom and export options
    st.subheader("📊 Server Performance Metrics")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.plotly_chart(fig_cpu, use_container_width=True)
        st.download_button("Download CPU Data", df.to_csv(index=False), file_name="cpu_data.csv")

    with col2:
        st.plotly_chart(fig_memory, use_container_width=True)
        st.download_button("Download Memory Data", df.to_csv(index=False), file_name="memory_data.csv")

    with col3:
        st.plotly_chart(fig_gc, use_container_width=True)
        st.download_button("Download GC Data", df.to_csv(index=False), file_name="gc_data.csv")
        
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

    st.dataframe(generate_transaction_data(), use_container_width=True)
    
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



