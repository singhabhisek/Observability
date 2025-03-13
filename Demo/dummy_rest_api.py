from flask import Flask, Response, request
import csv
from io import StringIO
from datetime import datetime, timedelta
import random

app = Flask(__name__)

# Define metric ranges
METRIC_RANGES = {
    "builtin:host.cpu.usage": (5.0, 60.0),
    "builtin:host.memory.usage": (30.0, 80.0),
    "builtin:host.disk.io": (100.0, 500.0),
}
DEFAULT_RANGE = (10.0, 50.0)

# Granularity mapping
GRANULARITY_MAP = {
    "1m": timedelta(minutes=1),
    "5m": timedelta(minutes=5),
    "15m": timedelta(minutes=15),
    "1h": timedelta(hours=1),
}

# Function to generate CSV data with spikes
def generate_csv_data(metric_ids, start_time, end_time, granularity):
    headers = ["metricId", "dt.entity.host", "time", "value"]
    hosts = ["HOST-000553947E276A2C", "HOST-123456789ABCDEF"]
    rows = []
    
    time_range_seconds = (end_time - start_time).total_seconds()
    if time_range_seconds < 2 * granularity.total_seconds():
        return ""

    # Generate 4-5 random spike intervals
    num_spikes = random.randint(4, 5)
    spike_times = set()

    for _ in range(num_spikes):
        spike_time = start_time + timedelta(seconds=random.randint(0, int(time_range_seconds)))
        spike_times.add(spike_time.replace(second=0, microsecond=0))

        # 50% chance of consecutive 5-minute spikes
        if random.random() < 0.5:
            for i in range(1, 5):  # Add next 4 minutes to create a 5-minute spike
                spike_times.add((spike_time + timedelta(minutes=i)).replace(second=0, microsecond=0))

    print(f"📌 Spike intervals: {sorted(spike_times)}")  # Debugging

    current_time = start_time
    while current_time <= end_time:
        time_key = current_time.replace(second=0, microsecond=0)  # Remove microseconds for precise comparison
        
        for metric_id in metric_ids:
            for host in hosts:
                min_val, max_val = METRIC_RANGES.get(metric_id, DEFAULT_RANGE)
                value = round(random.uniform(min_val, max_val), 2)

                # **Check if current time is in a spike interval**
                if time_key in spike_times:
                    spike_factor = random.uniform(2, 5)  # Apply a strong spike
                    value = round(value * spike_factor, 2) 
                    value = random.uniform(85,95) if value > 90 else value
                    print(f"🚀 SPIKE at {time_key} for {metric_id} | {host} → New Value: {value}")  # Debug

                # # **Introduce Missing Data Sometimes**
                # if random.random() < 0.1:  # 10% chance of missing data
                #     value = ""  # Simulate missing values

                rows.append([metric_id, host, current_time.strftime("%Y-%m-%dT%H:%M:%S"), value])

        current_time += granularity

    # Convert to CSV
    output = StringIO()
    csv_writer = csv.writer(output)
    csv_writer.writerow(headers)
    csv_writer.writerows(rows)
    return output.getvalue()

@app.route("/metrics", methods=["GET"])
def get_metrics():
    try:
        metric_ids = request.args.getlist("metricId")
        from_time_str = request.args.get("from")
        now_time_str = request.args.get("now")
        granularity_str = request.args.get("granularity", "1m")

        if not metric_ids or not from_time_str or not now_time_str:
            return Response("Error: 'metricId', 'from', and 'now' are required", status=400)

        # Parse timestamps
        try:
            start_time = datetime.fromisoformat(from_time_str.replace("Z", "+00:00"))
            end_time = datetime.fromisoformat(now_time_str.replace("Z", "+00:00"))
        except ValueError:
            return Response("Error: Invalid datetime format", status=400)

        # Validate granularity
        granularity = GRANULARITY_MAP.get(granularity_str)
        if not granularity:
            return Response("Error: Invalid granularity (use 1m, 5m, 15m, 1h)", status=400)

        csv_data = generate_csv_data(metric_ids, start_time, end_time, granularity)
        return Response(csv_data, mimetype="text/csv")

    except Exception as e:
        return Response(f"Error: {str(e)}", status=500)

if __name__ == "__main__":
    app.run(debug=True)
