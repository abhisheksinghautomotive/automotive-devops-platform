import requests
import random
import time
import json
import argparse
import os

DEFAULT_API_KEY = "local-secret"
FAILURE_STREAK_LIMIT = 5

def build_random_payload():
    return {
        "vehicle_id": f"veh-{random.randint(1,20):02}",
        "can_id": random.choice(["0x1F4", "0x101", "0x2A0", "0x2B0", "0x3C0"]),
        "payload" : {
            "eng-rpm": random.randint(800,2500),
            "speed_kph": random.randint(0,120),
            "coolant_temp_c": random.randint(70,100)
        }
    }

parser = argparse.ArgumentParser(description="Send test telemetry messages to the ingest API")
parser.add_argument("--count", type=int, default=10, help="Total number of messages to send")
parser.add_argument("--rate", type=float, default=10.0, help="Messages per second")
parser.add_argument("--host", type=str, default="http://127.0.0.1:8000", help="API host")
parser.add_argument("--api-key", type=str, default=DEFAULT_API_KEY, help="API key")
parser.add_argument("--dry-run", action="store_true", help="Enable dry-run mode (no messages sent)")
#TODO:
# parser.add_argument("--pattern", type=str, choices=["steady", "burst"], default="steady", help="Message sending pattern")
# parser.add_argument("--burst-size", type=int, default=20, help="Number of messages per burst (if pattern is burst)")
# parser.add_argument("--burst-interval", type=float, default=2.0, help="Interval between bursts in seconds (if pattern is burst)")
# parser.add_argument("--jitter", type=float, default=0.20, help="Max random jitter to add to intervals (as fraction, e.g. 0.1 = 10%%)")
# parser.add_argument("--from-jsonl", type=str, help="Path to JSONL file to read messages from")
# parser.add_argument("--summary-json", type=str, help="Path to write summary JSON report")
# parser.add_argument("--failure-streak-limit", type=int, default=FAILURE_STREAK_LIMIT, help="Abort after this many consecutive failures")


args = parser.parse_args()

# API key resolution
if args.api_key == DEFAULT_API_KEY:
    api_key_env = os.environ.get("API_KEY")
    if api_key_env:
        args.api_key = api_key_env
    else:
        print("Error: API key not provided via --api-key or API_KEY environment variable.")
        exit(1)

if args.api_key in ["local-secret", "changeme", ""]:
    print("Warning: Using placeholder API key. This is not suitable for production.")

# Dry-run mode
if args.dry_run:
    print("Dry-run mode: generating sample payloads")
    for _ in range(3):
        payload = build_random_payload()
        print(json.dumps(payload, indent=2))
    print("Dry-run mode: 3 messages generated (no network calls)")
    exit(0)




def main():
    derive_interval = 1.0 / args.rate if args.rate > 0 else 0
    url = args.host.rstrip("/") + "/ingest"
    success = 0
    fail = 0
    consecutive_failures = 0
    latencies_min = float("inf")
    latencies_max = float("-inf")
    attempted = 0
    latency_sum = 0.0
    latency_count = 0
    progress_interval = max(1, min(100, args.count // 10))
    start_time_message = time.time()
    for i in range(args.count):
        payload = build_random_payload()
        try:
            start_time = time.time()
            response = requests.post(url, json=payload, headers={"x-api-key": args.api_key})
            if response.status_code == 200:
                success += 1
                consecutive_failures = 0
                end_time = time.time()
                latency = (end_time - start_time) * 1000  # Convert to milliseconds
                latency_sum += latency
                latency_count += 1
                latencies_min = min(latencies_min, latency)
                latencies_max = max(latencies_max, latency)
            else:
                fail += 1
                consecutive_failures += 1
        except Exception as e:
            fail += 1
            consecutive_failures += 1
            print(f"Exception sending message: {e}")
        attempted += 1
        if (i+1) % progress_interval == 0:
            pct = ((i+1) / args.count) * 100
            print(f"[progress] {i+1}/{args.count} ({pct:.1f}%) success={success} fail={fail}")
        if consecutive_failures >= FAILURE_STREAK_LIMIT:
            print(f"Aborted early after {i+1} attempts due to {FAILURE_STREAK_LIMIT} consecutive failures.")
            break
        if derive_interval > 0:
            time.sleep(derive_interval)

    elapsed = time.time() - start_time_message

    average_latency = latency_sum / latency_count if latency_count > 0 else 0

    if latency_count == 0:
        latencies_min_display = 0
        latencies_max_display = 0
        average_latency_display = 0
    else:
        latencies_min_display = latencies_min
        latencies_max_display = latencies_max
        average_latency_display = average_latency

    success_rate_per_second = success / elapsed if elapsed > 0 else 0

    print(f"Requested: {args.count} Attempted: {attempted}")
    if attempted != args.count:
        print("Note: ended early (failure streak)")
    print(f"Success: {success}")
    print(f"Fail: {fail}")
    print(f"Elapsed Time: {elapsed:.1f}s")
    print(f"Attempted Rate: {attempted/elapsed:.1f} msg/s")
    print(f"Achieved Rate: {success_rate_per_second:.1f} msg/s")
    print(f"Success Rate: {success/attempted:.1f} msg/s" if attempted > 0 else "Success Rate: N/A")
    print(f"Latencies: min {latencies_min_display:.3f}ms, max {latencies_max_display:.3f}ms, avg {average_latency_display:.3f}ms")

if __name__ == "__main__":
    main()
