"""Event generator for battery cell telemetry."""

import random
from abc import ABC, abstractmethod
from typing import List, Tuple

from .models import BatteryModule, TelemetryEvent


class EventGeneratorInterface(ABC):
    """Interface for event generators following Interface Segregation Principle."""

    @abstractmethod
    def generate_events(self, num_events: int) -> List[TelemetryEvent]:
        """Generate a list of telemetry events."""
        raise NotImplementedError


class BatteryEventGenerator(EventGeneratorInterface):
    """Concrete implementation of battery telemetry event generator.

    Follows Single Responsibility Principle by focusing only on event generation.
    """

    def __init__(
        self,
        num_modules: int = 4,
        voltage_range: Tuple[int, int] = (3400, 4150),
        offset_range: Tuple[int, int] = (-40, 40),
    ):
        """Initialize the battery event generator.

        Args:
            num_modules: Number of battery modules/cells
            voltage_range: Min/max base voltage range in mV
            offset_range: Module offset variance range in mV
        """
        self.num_modules = num_modules
        self.voltage_range = voltage_range
        self.offset_range = offset_range

        # Pre-generate module offsets for consistency
        self.module_offsets = [
            random.randint(*offset_range) for _ in range(num_modules)
        ]

    def generate_events(self, num_events: int) -> List[TelemetryEvent]:
        """Generate battery telemetry events with realistic voltage variations.

        Args:
            num_events: Number of events to generate

        Returns:
            List of TelemetryEvent objects
        """
        events = []

        for sequence_num in range(num_events):
            modules = self._generate_modules()
            event = TelemetryEvent.create_new(sequence_num, modules)
            events.append(event)

        return events

    def _generate_modules(self) -> List[BatteryModule]:
        """Generate battery modules with voltage variations."""
        modules = []

        for module_id in range(self.num_modules):
            base_voltage = random.randint(*self.voltage_range)
            offset = self.module_offsets[module_id]

            module = BatteryModule(
                module_id=module_id, base_voltage=base_voltage, offset=offset
            )
            modules.append(module)

        return modules


# Factory pattern for creating generators
class EventGeneratorFactory:
    """Factory for creating event generators."""

    @staticmethod
    def create_battery_generator(**kwargs) -> BatteryEventGenerator:
        """Create a battery event generator with optional parameters."""
        return BatteryEventGenerator(**kwargs)


# Alias for backward compatibility
EventGenerator = BatteryEventGenerator
