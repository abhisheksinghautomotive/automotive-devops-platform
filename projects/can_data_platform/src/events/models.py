"""Data models for telemetry events."""

import time
from dataclasses import dataclass
from typing import Dict, List, Any
from uuid import uuid4


@dataclass
class BatteryModule:
    """Represents a single battery module with voltage characteristics."""

    module_id: int
    base_voltage: int
    offset: int

    @property
    def voltage(self) -> int:
        """Calculate the actual voltage including offset."""
        return max(0, self.base_voltage + self.offset)


@dataclass
class TelemetryEvent:
    """Represents a single telemetry event with battery data."""

    event_id: str
    sequence_number: int
    epoch_timestamp: float
    generation_time: int
    modules: List[BatteryModule]

    @classmethod
    def create_new(
        cls, sequence_number: int, modules: List[BatteryModule]
    ) -> "TelemetryEvent":
        """Create a new telemetry event with current timestamp."""
        return cls(
            event_id=str(uuid4()),
            sequence_number=sequence_number,
            epoch_timestamp=time.time(),
            generation_time=time.time_ns(),
            modules=modules,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the event to a dictionary for serialization."""
        event_dict = {
            "event_id": self.event_id,
            "sequence_number": self.sequence_number,
            "epoch_timestamp": self.epoch_timestamp,
            "generation_time": self.generation_time,
        }

        # Add dynamic cell voltage fields
        for i, module in enumerate(self.modules, 1):
            event_dict[f"Cell{i}Voltage"] = module.voltage

        # Add calculated statistics
        voltages = [module.voltage for module in self.modules]
        event_dict.update(
            {
                "min_voltage": min(voltages),
                "max_voltage": max(voltages),
                "avg_voltage": round(sum(voltages) / len(voltages)),
                "voltage_spread": max(voltages) - min(voltages),
                "module_offsets": [module.offset for module in self.modules],
                "num_modules": len(self.modules),
            }
        )

        return event_dict
