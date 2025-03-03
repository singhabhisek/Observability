import random
import datetime

# Define a list of sample URLs to simulate traffic
URLS = [
    "/home", "/login", "/checkout", "/api/getUserData", "/search?q=product",
    "/api/cart/add", "/api/cart/remove", "/products/latest", "/api/recommendations",
    "/api/shipping/rates", "/api/orders/recent", "/user/profile/update", 
    "/api/payment/initiate", "/checkout/confirmation", "/api/support/chat",
    "/search?q=phone", "/search?q=laptop", "/api/analytics/events", "/blog/latest",
    "/contact-us", "/api/notifications", "/api/user/preferences", "/account/settings",
    "/api/payment/status", "/home/featured", "/api/inventory/stock", "/search?q=tv",
    "/faq", "/api/location/detect", "/api/discounts", "/products/popular", "/api/user/logout",
    "/cart/view", "/api/giftcards", "/api/refunds/status", "/terms-of-service",
    "/search?q=headphones", "/api/newsletter/subscribe", "/privacy-policy",
    "/api/social/connect", "/api/loyalty/rewards", "/search?q=watch", "/api/download/app",
    "/products/sale", "/api/support/ticket", "/about-us", "/api/reviews/latest",
    "/api/tracking/order", "/api/wishlist/add"
]

# Generate IIS traffic logs for the past 2 days at 5-minute intervals
def generate_iis_logs(filename, days=2, interval_minutes=5):
    start_time = datetime.datetime.now() - datetime.timedelta(days=days)
    
    with open(filename, "w") as file:
        # Write header
        file.write("timestamp\tURL\tcount\taverage (ms)\tp90 (ms)\n")

        current_time = start_time
        while current_time <= datetime.datetime.now():
            for _ in range(50):  # Generate 50 records per interval
                url = random.choice(URLS)
                count = random.randint(100, 5000)
                avg_response = random.randint(120, 300)
                p90_response = avg_response + random.randint(50, 400)

                # Write to file
                file.write(f"{current_time.strftime('%Y-%m-%d %H:%M')}\t{url}\t{count}\t{avg_response}\t{p90_response}\n")

            # Move to the next 5-minute interval
            current_time += datetime.timedelta(minutes=interval_minutes)

    print(f"✅ IIS web traffic log generated: {filename}")

# Run the function
generate_iis_logs("iis_web_traffic_analysis.txt", days=2)
