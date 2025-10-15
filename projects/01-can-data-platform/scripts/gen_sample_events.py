"""Generate sample events for battery cell voltages and write to a JSONL file."""

import random
import json

with open("projects/01-can-data-platform/docs/sample-events-mvp.jsonl", "w") as f:
    for _ in range(10):
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
