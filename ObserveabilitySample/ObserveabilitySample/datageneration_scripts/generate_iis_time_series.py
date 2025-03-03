import random
import datetime

# Define the list of URLs to track
URLS = ["/home", "/login", "/checkout", "/api/getUserData"]

# Function to generate IIS time-series log data
def generate_iis_time_series(filename, days=2, interval_minutes=5):
    start_time = datetime.datetime.now() - datetime.timedelta(days=days)

    with open(filename, "w") as file:
        # Write header
        file.write("time\t" + "\t".join(URLS) + "\n")

        # Generate data for each time interval
        current_time = start_time
        while current_time <= datetime.datetime.now():
            response_times = [random.randint(100, 300) for _ in URLS]  # Generate random response times
            
            # Write time and response times to file
            file.write(current_time.strftime("%Y-%m-%d %H:%M:%S") + "\t" + "\t".join(map(str, response_times)) + "\n")

            # Increment time by the given interval (default: 5 minutes)
            current_time += datetime.timedelta(minutes=interval_minutes)

    print(f"✅ IIS time-series log generated: {filename}")

# Run the function
generate_iis_time_series("./iis_time_series.txt", days=2, interval_minutes=5)
