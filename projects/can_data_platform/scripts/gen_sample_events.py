"""Module to generate sample battery cell events with module-to-module."""

import random
import json
import argparse


def generate_events(num_events, num_modules=4, offset_range=(-40, 40)):
    """Generate sample battery events with module-to-module voltage variance.

    Args:
        num_events (int): Number of events to generate.
        num_modules (int): Number of cell modules in each event.
        offset_range (tuple): Range of variance for module offsets.

    Returns:
        list: List of event dictionaries.
    """
    # Create a fixed random offset for each module, applied across all events.
    module_offsets = [random.randint(*offset_range)
                      for _ in range(num_modules)]
    events = []
    for _ in range(num_events):
        module_voltages = []
        for idx in range(num_modules):
            # Sim base voltage
            base_voltage = random.randint(3400, 4150)
            noisy_voltage = base_voltage + module_offsets[idx]
            module_voltages.append(noisy_voltage)
        event = {
            "Cell1Voltage": module_voltages[0],
            "Cell2Voltage": module_voltages[1],
            "Cell3Voltage": module_voltages[2],
            "Cell4Voltage": module_voltages[3],
            "min_voltage": min(module_voltages),
            "max_voltage": max(module_voltages),
            "avg_voltage": round(sum(module_voltages) / num_modules),
            "module_offsets": list(module_offsets)  # for audit/debug
        }
        events.append(event)
    return events


def main():
    """Entrypoint for CLI generation of sample events."""
    parser = argparse.ArgumentParser(
        description="Generate sample battery cell events with module variance."
    )
    parser.add_argument(
        "--events", type=int, default=10, help="Number of sample events"
    )
    parser.add_argument(
        "--output", type=str, default="../../docs/sample_events_mvp.jsonl",
        help="Output JSONL file path"
    )
    args = parser.parse_args()

    events = generate_events(args.events)
    with open(args.output, "w", encoding="utf-8") as f:
        for event in events:
            f.write(json.dumps(event) + "\n")
    print(f"Wrote {args.events} events to {args.output}")


if __name__ == "__main__":
    main()
