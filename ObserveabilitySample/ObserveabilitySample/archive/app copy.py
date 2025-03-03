from flask import Flask, render_template, request, jsonify
import random
import requests
from datetime import datetime, timedelta

app = Flask(__name__)

import random
from datetime import datetime, timedelta

# Splunk API Configuration
SPLUNK_HOST = "https://splunk-server:8089"
SPLUNK_USERNAME = "admin"
SPLUNK_PASSWORD = "password"

# Define Splunk queries and their mock data files
data_sources = {
    "web_traffic": {
        "query": "search index=web_logs | stats count, avg(response_time) as avg_time, perc90(response_time) as p90 by url",
        "mock_file": "mock_data/iis_web_traffic_analysis.txt"
    },
    "error_logs": {
        "query": "search index=error_logs status>=500 | stats count by status, url",
        "mock_file": "mock_data/iis_error_logs.txt"
    },
    "response_times": {
        "query": "search index=web_logs | timechart avg(response_time) by url span=5m",
        "mock_file": "mock_data/iis_time_series.txt"
    }
}


############ DUMMY LOG SECTION START #############

LOG_MESSAGES = [
    "User {user} logged in from IP {ip}",
    "Failed login attempt for user {user} from IP {ip}",
    "Transaction {transaction} completed successfully in {time} ms",
    "Server {server} CPU usage at {usage}%",
    "Memory usage alert on {server}: {usage}%",
    "Error 500: Internal server error on {server}",
    "Database query executed: {query}",
    "User {user} logged out",
    "New order placed by {user}, Order ID: {order_id}",
    "Cache cleared on server {server}",
    "Security Alert: Multiple failed logins detected for {user}",
    "File upload successful: {filename} ({size}MB)",
    "API request received: {endpoint}, Response time: {time}ms",
    "Service {service} restarted on {server}",
    "Email sent to {email} for order confirmation",
]

def generate_realistic_logs(servers, num_logs=50):
    logs = []
    for _ in range(num_logs):
        log_template = random.choice(LOG_MESSAGES)
        log_message = log_template.format(
            user=f"user{random.randint(1, 100)}",
            ip=f"192.168.1.{random.randint(1, 255)}",
            transaction=random.choice(["Checkout", "Payment", "Login", "Search"]),
            time=random.randint(100, 2000),
            server=random.choice(servers) if servers else "Unknown Server",
            usage=random.randint(50, 99),
            query=f"SELECT * FROM users WHERE id={random.randint(1, 500)}",
            order_id=random.randint(1000, 9999),
            filename=f"report_{random.randint(1, 50)}.csv",
            size=round(random.uniform(0.5, 10.0), 2),
            endpoint=f"/api/{random.choice(['login', 'order', 'payment', 'profile'])}",
            service=random.choice(["AuthService", "OrderService", "CacheService"]),
            email=f"user{random.randint(1, 100)}@example.com"
        )
        logs.append({
            "timestamp": (datetime.now() - timedelta(minutes=random.randint(1, 60))).strftime("%Y-%m-%d %H:%M:%S"),
            "server": random.choice(servers) if servers else "Unknown",
            "message": log_message
        })
    return logs

############ DUMMY LOG SECTION END #############

###########SERVER CONFIGURATION#############
CONFIG = {
    "applications": {
        "App1": ["Server1", "Server2"],
        "App2": ["Server3", "Server4", "Server5", "Server6", "Server7", "Server8", "Server9"]
    }
}


########## GRANULARITY MAPPING #############

GRANULARITY_MAPPING = {
    "1m": 1,    # Every 1 minute
    "5m": 5,    # Every 5 minutes
    "15m": 15,  # Every 15 minutes
    "1h": 60    # Every 1 hour
}

######## CODE STARTS####################


####### SPLUNK CODE PART BEGINS #########################

# Function to execute a real Splunk query
def execute_splunk_query(query):
    url = f"{SPLUNK_HOST}/services/search/jobs"
    auth = (SPLUNK_USERNAME, SPLUNK_PASSWORD)
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "search": f"search {query}",
        "output_mode": "json",
        "exec_mode": "blocking"
    }

    # Submit search job
    response = requests.post(url, auth=auth, headers=headers, data=data, verify=False)
    if response.status_code != 201:
        return {"error": f"Failed to submit query: {response.text}"}

    # Extract job ID
    job_id = response.json()["sid"]

    # Retrieve search results
    results_url = f"{SPLUNK_HOST}/services/search/jobs/{job_id}/results?output_mode=json"
    results_response = requests.get(results_url, auth=auth, verify=False)
    if results_response.status_code != 200:
        return {"error": f"Failed to fetch results: {results_response.text}"}

    return results_response.json()["results"]

# Function to read mock data from a file
def read_mock_data(file_path):
    if not os.path.exists(file_path):
        return {"error": f"Mock data file {file_path} not found"}

    with open(file_path, "r") as file:
        lines = file.readlines()

    if len(lines) < 2:
        return {"error": f"File {file_path} is empty or missing data"}

    headers = lines[0].strip().split("\t")  # Extract headers from the first row
    data = [dict(zip(headers, line.strip().split("\t"))) for line in lines[1:]]
    
    return data

# API Endpoint to fetch data (mock or real)
@app.route("/fetch_splunk_data", methods=["GET"])
def fetch_splunk_data():
    mode = request.args.get("mode", "mock")  # Default to mock mode

    results = {}
    for key, source in data_sources.items():
        if mode == "real":
            results[key] = execute_splunk_query(source["query"])
        else:
            results[key] = read_mock_data(source["mock_file"])

    return jsonify(results)

####### SPLUNK CODE PART ENDS #########################

###### SIMULATE HOST SERVER HEALTH HONEYCOMB DATA ############

@app.route('/get_host_health', methods=['GET'])
def get_host_health():
    """ Simulating host health metrics dynamically """
    servers = ["Server1", "Server2", "Server3", "Server4", "Server5"]
    health_data = []
        
    for server in servers:
        cpu_usage = random.randint(10, 30)
        memory_usage = random.randint(10, 95)
        error_count = random.randint(0, 10)  # Simulating error occurrences
        
        # Determine server status based on CPU & errors
        if cpu_usage > 85 or error_count > 5:
            status = "Critical"  # 🔴 Red
        elif memory_usage > 70 or error_count > 2:
            status = "Warning"  # 🟠 Amber
        else:
            status = "Healthy"  # 🟢 Green
        
        health_data.append({
            "server": server,
            "cpu_usage": cpu_usage,
            "memory_usage": memory_usage,
            "error_count": error_count,
            "status": status
        })

    summary = {
        "cpu_avg": sum(d["cpu_usage"] for d in health_data) // len(health_data),
        "memory_avg": sum(d["memory_usage"] for d in health_data) // len(health_data),
        "total_errors": sum(d["error_count"] for d in health_data)
    }
    
    return jsonify({"health_data": health_data, "summary": summary})

############## HONEYCOMB SIMULATION ENDS ##################



@app.route('/')
def index():
    return render_template('dashboard.html', config=CONFIG)


#Filter the data based on the conditions passed from the UI Web

@app.route('/get_data', methods=['POST'])
def get_data():
    filters = request.json
    application = filters.get("application")
    start_date = filters.get("start_date")
    end_date = filters.get("end_date")
    selected_servers = filters.get("servers", [])  # Get selected servers
    granularity = filters.get("granularity", "5m")  # Default to 5 min
    servers = CONFIG["applications"].get(application, [])

    if not selected_servers:
        selected_servers = servers
    
    # Convert string dates to datetime objects
    # start_dt = datetime.strptime(start_date, "%Y-%m-%dT%H:%M") if start_date else datetime.now() - timedelta(hours=1)
    # end_dt = datetime.strptime(end_date, "%Y-%m-%dT%H:%M") if end_date else datetime.now()
    
    start_dt = datetime.strptime(start_date, "%Y-%m-%dT%H:%M") if start_date else datetime.now() - timedelta(hours=1)
    end_dt = datetime.strptime(end_date, "%Y-%m-%dT%H:%M") if end_date else datetime.now()

    # Get the interval (in minutes)
    interval = GRANULARITY_MAPPING.get(granularity, 5)

    # Generate timestamps every 5 minutes
    # timestamps = [(start_dt + timedelta(minutes=i)).strftime("%H:%M") for i in range(0, int((end_dt - start_dt).total_seconds() / 60), 5)]
    timestamps = [(start_dt + timedelta(minutes=i)).strftime("%H:%M") for i in range(0, int((end_dt - start_dt).total_seconds() / 60), interval)]

    transaction_types = [
        "Login", "Search", "Checkout", "Add to Cart", "Remove from Cart", 
        "Payment", "View Product", "Update Profile", "Logout", "Order History"
    ]
    
    transactions = {}
    transaction_summary = []

    for transaction in transaction_types:
        response_times = [round(random.uniform(0.5, 3.0), 2) for _ in timestamps]
        tps_values = [random.randint(5, 20) for _ in timestamps]  # Random TPS per timestamp
        
        avg_response_time = round(sum(response_times) / len(response_times), 2)
        avg_tps = round(sum(tps_values) / len(tps_values), 2)
        
        transactions[transaction] = {
            "response_times": response_times,
            "tps_values": tps_values
        }
        
        transaction_summary.append({
            "name": transaction,
            "tps": avg_tps,
            "avg_response_time": avg_response_time
        })

    status_codes = {"200": random.randint(100, 500), "400": random.randint(10, 50),"400": random.randint(10, 50),
                    "401": random.randint(10, 50),
                     "403": random.randint(10, 50),
                      "502": random.randint(100, 500), "500": random.randint(5, 20)}

    # cpu_usage = {s: [random.randint(10, 90) for _ in timestamps] for s in servers}
    # memory_usage = {s: [random.randint(20, 80) for _ in timestamps] for s in servers}
    # server_hits = {s: random.randint(50, 300) for s in servers}
    cpu_usage = {s: [random.randint(10, 90) for _ in timestamps] for s in selected_servers}
    memory_usage = {s: [random.randint(20, 80) for _ in timestamps] for s in selected_servers}
    server_hits = {s: random.randint(50, 300) for s in selected_servers}


    # logs = [{"timestamp": (datetime.now() - timedelta(minutes=i)).strftime("%Y-%m-%d %H:%M:%S"), 
    #          "server": random.choice(servers), "message": "Sample log entry"} for i in range(50)]
    
    # logs = [{"timestamp": (datetime.now() - timedelta(minutes=i)).strftime("%Y-%m-%d %H:%M:%S"), 
    #             "server": random.choice(selected_servers), "message": "Sample log entry"} for i in range(50) if selected_servers]

    logs = generate_realistic_logs(selected_servers, num_logs=50)
    
    return jsonify({
        "timestamps": timestamps,
        "transactions": transactions,
        "transaction_summary": transaction_summary,
        "status_codes": status_codes,
        "cpu_usage": cpu_usage,
        "server_hits": server_hits,
        "memory_usage": memory_usage,
        "logs": logs
    })

if __name__ == '__main__':
    app.run(debug=True)
