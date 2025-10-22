"""Message processing modules for SQS consumer."""

from .interfaces import MessageProcessor, ProcessingResult
from .telemetry_processor import TelemetryMessageProcessor

__all__ = ["MessageProcessor", "ProcessingResult", "TelemetryMessageProcessor"]
