"""Telemetry-specific message processor implementation."""

import logging
from typing import Dict, Any, Optional

from .interfaces import BaseMessageProcessor, ProcessingResult


logger = logging.getLogger(__name__)


class TelemetryMessageProcessor(BaseMessageProcessor):
    """Processor for battery telemetry messages.

    Follows Single Responsibility Principle.
    Handles CAN bus telemetry events with validation and processing logic.
    """

    def __init__(self):
        """Initialize telemetry message processor."""
        super().__init__("TelemetryProcessor")

        # Expected fields in telemetry events
        self.required_fields = {
            "Cell1Voltage",
            "Cell2Voltage",
            "Cell3Voltage",
            "Cell4Voltage",
        }
        self.optional_fields = {
            "min_voltage",
            "max_voltage",
            "avg_voltage",
            "voltage_spread",
            "module_offsets",
            "num_modules",
            "event_id",
            "sequence_number",
        }

    def process_parsed_event(
        self, event_data: Dict[str, Any], event_timestamp: Optional[float]
    ) -> ProcessingResult:
        """Process a parsed telemetry event with validation.

        Args:
            event_data: Parsed telemetry event dictionary
            event_timestamp: Extracted event timestamp

        Returns:
            ProcessingResult with processing outcome
        """
        # Validate required fields
        validation_result = self._validate_telemetry_event(event_data)
        if not validation_result.success:
            return validation_result

        # Process telemetry data
        try:
            processed_data = self._process_telemetry_data(event_data)

            self.logger.info("Successfully processed telemetry event: %s", event_data)

            return ProcessingResult.success_result(
                event_timestamp=event_timestamp, processed_data=processed_data
            )

        except (KeyError, ValueError, TypeError, AttributeError) as e:
            error_msg = f"Telemetry processing failed: {e}"
            self.logger.error(error_msg)
            return ProcessingResult.failure_result(error_msg)

    def _validate_telemetry_event(self, event_data: Dict[str, Any]) -> ProcessingResult:
        """Validate that the event contains required telemetry fields.

        Args:
            event_data: Event data to validate

        Returns:
            ProcessingResult indicating validation success or failure
        """
        # Check for required voltage fields
        missing_fields = self.required_fields - set(event_data.keys())
        if missing_fields:
            error_msg = f"Missing required fields: {missing_fields}"
            self.logger.error(error_msg)
            return ProcessingResult.failure_result(error_msg)

        # Validate voltage values are numeric
        for field in self.required_fields:
            value = event_data[field]
            if not isinstance(value, (int, float)):
                error_msg = f"Invalid voltage value for {field}: {value}"
                self.logger.error(error_msg)
                return ProcessingResult.failure_result(error_msg)

        return ProcessingResult.success_result()

    def _process_telemetry_data(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process and enrich telemetry data.

        Args:
            event_data: Raw telemetry event data

        Returns:
            Processed and enriched telemetry data
        """
        # Extract voltage values
        voltages = [
            event_data["Cell1Voltage"],
            event_data["Cell2Voltage"],
            event_data["Cell3Voltage"],
            event_data["Cell4Voltage"],
        ]

        # Calculate derived metrics if not present
        processed_data = event_data.copy()

        if "min_voltage" not in processed_data:
            processed_data["min_voltage"] = min(voltages)

        if "max_voltage" not in processed_data:
            processed_data["max_voltage"] = max(voltages)

        if "avg_voltage" not in processed_data:
            processed_data["avg_voltage"] = round(sum(voltages) / len(voltages))

        if "voltage_spread" not in processed_data:
            processed_data["voltage_spread"] = max(voltages) - min(voltages)

        # Add processing metadata
        processed_data["processing_timestamp"] = self.extract_timestamp(processed_data)
        processed_data["processor_name"] = self.get_processor_name()

        return processed_data


class MessageProcessorFactory:
    """Factory for creating message processors."""

    @staticmethod
    def create_telemetry_processor() -> TelemetryMessageProcessor:
        """Create a telemetry message processor."""
        return TelemetryMessageProcessor()

    @staticmethod
    def create_default_processor() -> TelemetryMessageProcessor:
        """Create the default processor (currently telemetry)."""
        return TelemetryMessageProcessor()
