import requests
import json
import os
from datetime import datetime
import pytz  # Import timezone library
import urllib.parse

from datetime import datetime, timedelta, timezone

# EST is UTC-5 (Standard Time)
EST_OFFSET = timedelta(hours=-5)

def convert_utc_to_est(timestamp):
    """Convert UTC timestamp (in milliseconds) to EST manually."""
    utc_time = datetime.utcfromtimestamp(timestamp / 1000).replace(tzinfo=timezone.utc)
    est_time = utc_time + EST_OFFSET  # Convert to EST
    return est_time.strftime('%Y-%m-%d %H:%M:%S')

# Usage:
# timestamp = 1708915200000  # Example UTC timestamp (milliseconds)
# print(convert_utc_to_est(timestamp))

# Load Config
base_dir = os.path.dirname(os.path.abspath(__file__))  # Get script's directory
config_path = os.path.join(base_dir, "config.json")

with open(config_path, "r") as config_file:
    config = json.load(config_file)

DT_ENVIRONMENT = config["dynatrace"]["environment"]
DT_API_TOKEN = config["dynatrace"]["api_token"]
HEADERS = {"Authorization": f"Api-Token {DT_API_TOKEN}", "Content-Type": "application/json"}

# Define UTC and EST timezones
utc_tz = pytz.utc
est_tz = pytz.timezone('US/Eastern')

def get_hosts_by_management_zone(mz_name):
    url = f"{DT_ENVIRONMENT}/api/v2/entities?entitySelector=type(\"HOST\"),mzName(\"{mz_name}\")"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return {host["entityId"]: host["displayName"] for host in response.json().get("entities", [])}
    return {}

def get_metrics(entity_ids, metric_keys, start_time, end_time, granularity):
    entity_selector = ",".join(entity_ids)
    metric_selector = ",".join(metric_keys)
    
    url = (f"{DT_ENVIRONMENT}/api/v2/metrics/query?"
           f"metricSelector={metric_selector}&entitySelector=entityId(\"{entity_selector}\")"
           f"&from={start_time}&to={end_time}&resolution={granularity}")
    
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json().get("result", [])
    return []

def abcd():
    mz_name = config["applications"]["Mobile"]["management_zone"]  # Fetch from config
    app_name = "Mobile"  # Replace with an actual application name
    start_time = "now-1h"
    end_time = "now"
    granularity = "5m"

    servers_dict = get_hosts_by_management_zone(mz_name)
    selected_servers = list(servers_dict.keys())

    app_metrics = config["default_metrics"] + config["applications"].get(app_name, {}).get("metrics", [])
    metric_ids = [m["id"] for m in app_metrics]

    metrics_data = get_metrics(selected_servers, metric_ids, start_time, end_time, granularity)

    output = {metric["metricId"]: [] for metric in metrics_data}
    for metric in metrics_data:
        metric_name = metric["metricId"]
        for series in metric.get("data", []):
            server_id = series["dimensions"][0]
            server_name = servers_dict.get(server_id, "Unknown")
            for ts, value in zip(series["timestamps"], series["values"]):
                # Convert timestamp from UTC to EST
                utc_time = datetime.utcfromtimestamp(ts / 1000).replace(tzinfo=utc_tz)
                est_time = utc_time.astimezone(est_tz).strftime('%Y-%m-%d %H:%M:%S')

                output[metric_name].append({
                    "timestamp": est_time,
                    "server": server_name,
                    "value": value
                })

    print(json.dumps(output, indent=4))

if __name__ == "__main__":
    abcd()
