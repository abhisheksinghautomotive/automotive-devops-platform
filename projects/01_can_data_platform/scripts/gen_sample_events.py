"""Generate sample events for battery cell voltages and write to a JSONL file."""
import random
import json
import argparse

parser = argparse.ArgumentParser(description="Generate sample events for battery cell voltages.")
parser.add_argument("--events", type=int, default=10, help="Number of sample events to generate")
args = parser.parse_args()

with open("projects/01_can_data_platform/data/sample_events_mvp.jsonl", "w") as f:
    for _ in range(args.events):
        c1 = random.randint(3000, 4200)
        c4 = random.randint(3000, 4200)
        mn = min(c1, c4)
        mx = max(c1, c4)
        avg = int(round((c1 + c4) / 2))
        event = {
            "Cell_1_Voltage": c1,
            "Cell_4_Voltage": c4,
            "min_voltage": mn,
            "max_voltage": mx,
            "avg_voltage": avg
        }
        f.write(json.dumps(event) + "\n")
