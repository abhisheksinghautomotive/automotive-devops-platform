"""Comprehensive tests for events models."""

import time
import unittest
from unittest.mock import patch

from projects.can_data_platform.src.events.models import (
    BatteryModule,
    TelemetryEvent,
)


class TestBatteryModule(unittest.TestCase):
    """Test cases for BatteryModule class."""

    def test_initialization(self):
        """Test BatteryModule initialization."""
        module = BatteryModule(module_id=1, base_voltage=3500, offset=50)

        self.assertEqual(module.module_id, 1)
        self.assertEqual(module.base_voltage, 3500)
        self.assertEqual(module.offset, 50)

    def test_voltage_property_positive_offset(self):
        """Test voltage calculation with positive offset."""
        module = BatteryModule(module_id=1, base_voltage=3500, offset=50)

        self.assertEqual(module.voltage, 3550)

    def test_voltage_property_negative_offset(self):
        """Test voltage calculation with negative offset."""
        module = BatteryModule(module_id=1, base_voltage=3500, offset=-100)

        self.assertEqual(module.voltage, 3400)

    def test_voltage_property_zero_offset(self):
        """Test voltage calculation with zero offset."""
        module = BatteryModule(module_id=1, base_voltage=3500, offset=0)

        self.assertEqual(module.voltage, 3500)

    def test_voltage_property_negative_result_clamped_to_zero(self):
        """Test voltage calculation clamped to zero for negative results."""
        module = BatteryModule(module_id=1, base_voltage=100, offset=-200)

        # Should be clamped to 0, not -100
        self.assertEqual(module.voltage, 0)


class TestTelemetryEvent(unittest.TestCase):
    """Test cases for TelemetryEvent class."""

    def setUp(self):
        """Set up test fixtures."""
        self.modules = [
            BatteryModule(module_id=1, base_voltage=3500, offset=0),
            BatteryModule(module_id=2, base_voltage=3500, offset=50),
            BatteryModule(module_id=3, base_voltage=3500, offset=25),
            BatteryModule(module_id=4, base_voltage=3500, offset=75),
        ]

    def test_initialization(self):
        """Test TelemetryEvent initialization."""
        event = TelemetryEvent(
            event_id="test-123",
            sequence_number=1,
            epoch_timestamp=1234567890.5,
            generation_time=1234567890123456789,
            modules=self.modules,
        )

        self.assertEqual(event.event_id, "test-123")
        self.assertEqual(event.sequence_number, 1)
        self.assertEqual(event.epoch_timestamp, 1234567890.5)
        self.assertEqual(event.generation_time, 1234567890123456789)
        self.assertEqual(len(event.modules), 4)

    @patch('projects.can_data_platform.src.events.models.time.time')
    @patch('projects.can_data_platform.src.events.models.time.time_ns')
    @patch('projects.can_data_platform.src.events.models.uuid4')
    def test_create_new(self, mock_uuid, mock_time_ns, mock_time):
        """Test create_new factory method."""
        mock_uuid.return_value = "mock-uuid-123"
        mock_time.return_value = 1234567890.5
        mock_time_ns.return_value = 1234567890123456789

        event = TelemetryEvent.create_new(sequence_number=42, modules=self.modules)

        self.assertEqual(event.event_id, "mock-uuid-123")
        self.assertEqual(event.sequence_number, 42)
        self.assertEqual(event.epoch_timestamp, 1234567890.5)
        self.assertEqual(event.generation_time, 1234567890123456789)
        self.assertEqual(len(event.modules), 4)

    def test_to_dict_basic_fields(self):
        """Test to_dict includes basic event fields."""
        event = TelemetryEvent(
            event_id="test-123",
            sequence_number=1,
            epoch_timestamp=1234567890.5,
            generation_time=1234567890123456789,
            modules=self.modules,
        )

        result = event.to_dict()

        self.assertEqual(result["event_id"], "test-123")
        self.assertEqual(result["sequence_number"], 1)
        self.assertEqual(result["epoch_timestamp"], 1234567890.5)
        self.assertEqual(result["generation_time"], 1234567890123456789)

    def test_to_dict_cell_voltages(self):
        """Test to_dict includes dynamic cell voltage fields."""
        event = TelemetryEvent(
            event_id="test-123",
            sequence_number=1,
            epoch_timestamp=1234567890.5,
            generation_time=1234567890123456789,
            modules=self.modules,
        )

        result = event.to_dict()

        self.assertEqual(result["Cell1Voltage"], 3500)
        self.assertEqual(result["Cell2Voltage"], 3550)
        self.assertEqual(result["Cell3Voltage"], 3525)
        self.assertEqual(result["Cell4Voltage"], 3575)

    def test_to_dict_statistics(self):
        """Test to_dict includes calculated statistics."""
        event = TelemetryEvent(
            event_id="test-123",
            sequence_number=1,
            epoch_timestamp=1234567890.5,
            generation_time=1234567890123456789,
            modules=self.modules,
        )

        result = event.to_dict()

        self.assertEqual(result["min_voltage"], 3500)
        self.assertEqual(result["max_voltage"], 3575)
        self.assertEqual(result["avg_voltage"], 3538)  # Rounded
        self.assertEqual(result["voltage_spread"], 75)
        self.assertEqual(result["module_offsets"], [0, 50, 25, 75])
        self.assertEqual(result["num_modules"], 4)

    def test_to_dict_with_single_module(self):
        """Test to_dict with single module."""
        single_module = [BatteryModule(module_id=1, base_voltage=3500, offset=0)]
        event = TelemetryEvent(
            event_id="test-123",
            sequence_number=1,
            epoch_timestamp=time.time(),
            generation_time=time.time_ns(),
            modules=single_module,
        )

        result = event.to_dict()

        self.assertEqual(result["Cell1Voltage"], 3500)
        self.assertEqual(result["min_voltage"], 3500)
        self.assertEqual(result["max_voltage"], 3500)
        self.assertEqual(result["avg_voltage"], 3500)
        self.assertEqual(result["voltage_spread"], 0)
        self.assertEqual(result["num_modules"], 1)

    def test_to_dict_with_varying_voltages(self):
        """Test to_dict with widely varying voltages."""
        varied_modules = [
            BatteryModule(module_id=1, base_voltage=3000, offset=0),
            BatteryModule(module_id=2, base_voltage=3500, offset=100),
            BatteryModule(module_id=3, base_voltage=4000, offset=-200),
        ]
        event = TelemetryEvent(
            event_id="test-123",
            sequence_number=1,
            epoch_timestamp=time.time(),
            generation_time=time.time_ns(),
            modules=varied_modules,
        )

        result = event.to_dict()

        self.assertEqual(result["Cell1Voltage"], 3000)
        self.assertEqual(result["Cell2Voltage"], 3600)
        self.assertEqual(result["Cell3Voltage"], 3800)
        self.assertEqual(result["min_voltage"], 3000)
        self.assertEqual(result["max_voltage"], 3800)
        self.assertEqual(result["avg_voltage"], 3467)  # Rounded
        self.assertEqual(result["voltage_spread"], 800)

    def test_to_dict_with_negative_clamped_voltage(self):
        """Test to_dict with module that clamps to zero."""
        modules_with_zero = [
            BatteryModule(module_id=1, base_voltage=3500, offset=0),
            BatteryModule(module_id=2, base_voltage=100, offset=-200),  # Clamped to 0
        ]
        event = TelemetryEvent(
            event_id="test-123",
            sequence_number=1,
            epoch_timestamp=time.time(),
            generation_time=time.time_ns(),
            modules=modules_with_zero,
        )

        result = event.to_dict()

        self.assertEqual(result["Cell1Voltage"], 3500)
        self.assertEqual(result["Cell2Voltage"], 0)
        self.assertEqual(result["min_voltage"], 0)
        self.assertEqual(result["max_voltage"], 3500)


if __name__ == "__main__":
    unittest.main()
