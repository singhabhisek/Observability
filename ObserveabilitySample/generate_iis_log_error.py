import random
import datetime

# Define possible error status codes and messages
ERRORS = {
    500: "Internal Server Error",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Timeout"
}

# Define sample URLs that might generate errors
ERROR_URLS = [
    "/api/processPayment", "/api/getUserDetails", "/checkout", 
    "/api/externalRequest", "/api/processOrder", "/api/getOrderDetails"
]

# Sample server names
SERVERS = ["web-server-01", "web-server-02", "web-server-03", "web-server-04"]

# Function to generate a random error trace (2-3 lines)
def generate_error_trace():
    traces = [
        "Traceback (most recent call last):",
        "  File '/app/server.py', line 45, in process_request",
        "  raise Exception('Unexpected failure')",
        "ConnectionError: Failed to reach the database",
        "TimeoutError: The request took too long to process",
        "ValueError: Invalid input received",
        "KeyError: Missing required field in request"
    ]
    return "\n".join(random.sample(traces, k=3))  # Pick 3 random lines

# Function to generate IIS error logs for the past 2 days
def generate_iis_error_logs(filename, days=2, entries_per_day=10):
    start_date = datetime.datetime.now() - datetime.timedelta(days=days)

    with open(filename, "w") as file:
        # Write header
        file.write("Timestamp\tStatus\tURL\tCount\tError Message\tServer\tError Description\n")

        for day in range(days):
            current_date = start_date + datetime.timedelta(days=day)
            
            for _ in range(entries_per_day):
                timestamp = current_date + datetime.timedelta(
                    hours=random.randint(0, 23), minutes=random.randint(0, 59), seconds=random.randint(0, 59)
                )
                status = random.choice(list(ERRORS.keys()))
                url = random.choice(ERROR_URLS)
                count = random.randint(50, 200)
                error_message = ERRORS[status]
                server = random.choice(SERVERS)
                error_trace = generate_error_trace()

                # Write to file
                file.write(f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')}\t{status}\t{url}\t{count}\t{error_message}\t{server}\t{error_trace}\n")

    print(f"✅ IIS error log generated: {filename}")

# Run the function
generate_iis_error_logs("iis_error_logs.txt", days=2, entries_per_day=10)
