"""Unit tests for telemetry processor implementations."""

import unittest
from unittest.mock import patch

from projects.can_data_platform.src.processors.telemetry_processor import (
    MessageProcessorFactory,
    TelemetryMessageProcessor,
)


class TestTelemetryMessageProcessor(unittest.TestCase):
    """Test TelemetryMessageProcessor implementation."""

    def setUp(self):
        """Set up test environment."""
        self.processor = TelemetryMessageProcessor()

    def test_initialization(self):
        """Test processor initialization."""
        self.assertEqual(self.processor.get_processor_name(), "TelemetryProcessor")
        
        # Check required fields
        expected_required = {
            "Cell1Voltage",
            "Cell2Voltage",
            "Cell3Voltage",
            "Cell4Voltage",
        }
        self.assertEqual(self.processor.required_fields, expected_required)
        
        # Check optional fields
        expected_optional = {
            "min_voltage",
            "max_voltage",
            "avg_voltage",
            "voltage_spread",
            "module_offsets",
            "num_modules",
            "event_id",
            "sequence_number",
        }
        self.assertEqual(self.processor.optional_fields, expected_optional)

    def test_process_parsed_event_success(self):
        """Test successful event processing."""
        event_data = {
            "Cell1Voltage": 3500,
            "Cell2Voltage": 3550,
            "Cell3Voltage": 3525,
            "Cell4Voltage": 3575,
            "timestamp": "2024-01-01T00:00:00",
        }
        event_timestamp = 1640995200.0
        
        with patch.object(self.processor, 'extract_timestamp', return_value=1640995200.0):
            result = self.processor.process_parsed_event(event_data, event_timestamp)
        
        self.assertTrue(result.success)
        self.assertEqual(result.event_timestamp, event_timestamp)
        self.assertIsNotNone(result.processed_data)
        
        # Check derived metrics
        processed = result.processed_data
        self.assertEqual(processed["min_voltage"], 3500)
        self.assertEqual(processed["max_voltage"], 3575)
        self.assertEqual(processed["avg_voltage"], 3538)  # (3500+3550+3525+3575)/4
        self.assertEqual(processed["voltage_spread"], 75)  # 3575-3500
        self.assertEqual(processed["processor_name"], "TelemetryProcessor")
        self.assertEqual(processed["processing_timestamp"], 1640995200.0)

    def test_process_parsed_event_with_existing_metrics(self):
        """Test event processing when metrics already exist."""
        event_data = {
            "Cell1Voltage": 3500,
            "Cell2Voltage": 3550,
            "Cell3Voltage": 3525,
            "Cell4Voltage": 3575,
            "min_voltage": 3490,  # Pre-existing value
            "max_voltage": 3580,  # Pre-existing value
            "avg_voltage": 3540,  # Pre-existing value
            "voltage_spread": 90,  # Pre-existing value
        }
        event_timestamp = 1640995200.0
        
        with patch.object(self.processor, 'extract_timestamp', return_value=1640995200.0):
            result = self.processor.process_parsed_event(event_data, event_timestamp)
        
        self.assertTrue(result.success)
        processed = result.processed_data
        
        # Should keep existing values, not recalculate
        self.assertEqual(processed["min_voltage"], 3490)
        self.assertEqual(processed["max_voltage"], 3580)
        self.assertEqual(processed["avg_voltage"], 3540)
        self.assertEqual(processed["voltage_spread"], 90)

    def test_process_parsed_event_validation_failure(self):
        """Test event processing with validation failure."""
        event_data = {
            "Cell1Voltage": 3500,
            "Cell2Voltage": 3550,
            # Missing Cell3Voltage and Cell4Voltage
        }
        
        result = self.processor.process_parsed_event(event_data, 1640995200.0)
        
        self.assertFalse(result.success)
        self.assertIn("Missing required fields", result.error_message)

    def test_process_parsed_event_processing_exception(self):
        """Test event processing with processing exception."""
        event_data = {
            "Cell1Voltage": 3500,
            "Cell2Voltage": 3550,
            "Cell3Voltage": 3525,
            "Cell4Voltage": 3575,
        }
        
        # Mock extract_timestamp to raise an exception
        with patch.object(self.processor, 'extract_timestamp', side_effect=ValueError("Timestamp error")):
            result = self.processor.process_parsed_event(event_data, 1640995200.0)
        
        self.assertFalse(result.success)
        self.assertIn("Telemetry processing failed", result.error_message)

    def test_validate_telemetry_event_success(self):
        """Test successful telemetry event validation."""
        event_data = {
            "Cell1Voltage": 3500,
            "Cell2Voltage": 3550,
            "Cell3Voltage": 3525,
            "Cell4Voltage": 3575,
        }
        
        result = self.processor._validate_telemetry_event(event_data)
        
        self.assertTrue(result.success)

    def test_validate_telemetry_event_missing_fields(self):
        """Test telemetry event validation with missing fields."""
        event_data = {
            "Cell1Voltage": 3500,
            "Cell2Voltage": 3550,
            # Missing Cell3Voltage and Cell4Voltage
        }
        
        result = self.processor._validate_telemetry_event(event_data)
        
        self.assertFalse(result.success)
        self.assertIn("Missing required fields", result.error_message)
        self.assertIn("Cell3Voltage", result.error_message)
        self.assertIn("Cell4Voltage", result.error_message)

    def test_validate_telemetry_event_invalid_voltage_type(self):
        """Test telemetry event validation with invalid voltage type."""
        event_data = {
            "Cell1Voltage": 3500,
            "Cell2Voltage": "invalid",  # String instead of number
            "Cell3Voltage": 3525,
            "Cell4Voltage": 3575,
        }
        
        result = self.processor._validate_telemetry_event(event_data)
        
        self.assertFalse(result.success)
        self.assertIn("Invalid voltage value for Cell2Voltage", result.error_message)

    def test_validate_telemetry_event_none_voltage(self):
        """Test telemetry event validation with None voltage."""
        event_data = {
            "Cell1Voltage": 3500,
            "Cell2Voltage": 3550,
            "Cell3Voltage": None,  # None instead of number
            "Cell4Voltage": 3575,
        }
        
        result = self.processor._validate_telemetry_event(event_data)
        
        self.assertFalse(result.success)
        self.assertIn("Invalid voltage value for Cell3Voltage", result.error_message)

    def test_process_telemetry_data_basic(self):
        """Test basic telemetry data processing."""
        event_data = {
            "Cell1Voltage": 3500,
            "Cell2Voltage": 3550,
            "Cell3Voltage": 3525,
            "Cell4Voltage": 3575,
            "timestamp": "2024-01-01T00:00:00",
        }
        
        with patch.object(self.processor, 'extract_timestamp', return_value=1640995200.0):
            processed = self.processor._process_telemetry_data(event_data)
        
        # Check original data is preserved
        self.assertEqual(processed["Cell1Voltage"], 3500)
        self.assertEqual(processed["Cell2Voltage"], 3550)
        self.assertEqual(processed["Cell3Voltage"], 3525)
        self.assertEqual(processed["Cell4Voltage"], 3575)
        
        # Check derived metrics
        self.assertEqual(processed["min_voltage"], 3500)
        self.assertEqual(processed["max_voltage"], 3575)
        self.assertEqual(processed["avg_voltage"], 3538)
        self.assertEqual(processed["voltage_spread"], 75)
        
        # Check metadata
        self.assertEqual(processed["processing_timestamp"], 1640995200.0)
        self.assertEqual(processed["processor_name"], "TelemetryProcessor")

    def test_process_telemetry_data_with_float_voltages(self):
        """Test telemetry data processing with float voltages."""
        event_data = {
            "Cell1Voltage": 3500.5,
            "Cell2Voltage": 3550.7,
            "Cell3Voltage": 3525.2,
            "Cell4Voltage": 3575.1,
        }
        
        with patch.object(self.processor, 'extract_timestamp', return_value=1640995200.0):
            processed = self.processor._process_telemetry_data(event_data)
        
        # Check derived metrics with floats
        self.assertEqual(processed["min_voltage"], 3500.5)
        self.assertEqual(processed["max_voltage"], 3575.1)
        self.assertEqual(processed["avg_voltage"], 3538)  # rounded to int
        self.assertAlmostEqual(processed["voltage_spread"], 74.6, places=1)

    def test_process_telemetry_data_preserves_existing_metrics(self):
        """Test that existing derived metrics are preserved."""
        event_data = {
            "Cell1Voltage": 3500,
            "Cell2Voltage": 3550,
            "Cell3Voltage": 3525,
            "Cell4Voltage": 3575,
            "min_voltage": 3490,  # Pre-existing
            "max_voltage": 3580,  # Pre-existing
            "avg_voltage": 3540,  # Pre-existing
            "voltage_spread": 90,  # Pre-existing
        }
        
        with patch.object(self.processor, 'extract_timestamp', return_value=1640995200.0):
            processed = self.processor._process_telemetry_data(event_data)
        
        # Should preserve existing values
        self.assertEqual(processed["min_voltage"], 3490)
        self.assertEqual(processed["max_voltage"], 3580)
        self.assertEqual(processed["avg_voltage"], 3540)
        self.assertEqual(processed["voltage_spread"], 90)

    def test_process_telemetry_data_edge_case_equal_voltages(self):
        """Test telemetry data processing with equal voltages."""
        event_data = {
            "Cell1Voltage": 3550,
            "Cell2Voltage": 3550,
            "Cell3Voltage": 3550,
            "Cell4Voltage": 3550,
        }
        
        with patch.object(self.processor, 'extract_timestamp', return_value=1640995200.0):
            processed = self.processor._process_telemetry_data(event_data)
        
        # All metrics should be the same
        self.assertEqual(processed["min_voltage"], 3550)
        self.assertEqual(processed["max_voltage"], 3550)
        self.assertEqual(processed["avg_voltage"], 3550)
        self.assertEqual(processed["voltage_spread"], 0)

    def test_process_telemetry_data_additional_fields(self):
        """Test that additional fields are preserved during processing."""
        event_data = {
            "Cell1Voltage": 3500,
            "Cell2Voltage": 3550,
            "Cell3Voltage": 3525,
            "Cell4Voltage": 3575,
            "event_id": "evt_001",
            "sequence_number": 42,
            "module_offsets": [10, 20, 30],
            "custom_field": "custom_value",
        }
        
        with patch.object(self.processor, 'extract_timestamp', return_value=1640995200.0):
            processed = self.processor._process_telemetry_data(event_data)
        
        # Check additional fields are preserved
        self.assertEqual(processed["event_id"], "evt_001")
        self.assertEqual(processed["sequence_number"], 42)
        self.assertEqual(processed["module_offsets"], [10, 20, 30])
        self.assertEqual(processed["custom_field"], "custom_value")


class TestMessageProcessorFactory(unittest.TestCase):
    """Test MessageProcessorFactory implementation."""

    def test_create_telemetry_processor(self):
        """Test creating telemetry processor via factory."""
        processor = MessageProcessorFactory.create_telemetry_processor()
        
        self.assertIsInstance(processor, TelemetryMessageProcessor)
        self.assertEqual(processor.get_processor_name(), "TelemetryProcessor")

    def test_create_default_processor(self):
        """Test creating default processor via factory."""
        processor = MessageProcessorFactory.create_default_processor()
        
        self.assertIsInstance(processor, TelemetryMessageProcessor)
        self.assertEqual(processor.get_processor_name(), "TelemetryProcessor")

    def test_factory_creates_different_instances(self):
        """Test that factory creates separate instances."""
        processor1 = MessageProcessorFactory.create_telemetry_processor()
        processor2 = MessageProcessorFactory.create_telemetry_processor()
        
        self.assertIsInstance(processor1, TelemetryMessageProcessor)
        self.assertIsInstance(processor2, TelemetryMessageProcessor)
        self.assertIsNot(processor1, processor2)  # Different instances


if __name__ == "__main__":
    unittest.main()