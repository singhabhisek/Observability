

# Define the API endpoint
import requests


base_url = "http://127.0.0.1:5000/metrics"  # Update if running on a different host

# Set query parameters
params = {
    "metricId": "builtin:host.cpu.usage",  # Change to any metric ID
    # "days": 2,  # Fetch data for the last 2 days
    "hours": 4  # Uncomment to fetch data for last 4 hours instead of days
}

# Send a GET request
metrics_data = requests.get(base_url, params=params)
print (metrics_data.text)
