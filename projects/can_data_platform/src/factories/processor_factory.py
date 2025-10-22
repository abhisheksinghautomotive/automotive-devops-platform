"""Factory for creating message processor instances."""

from ..processors.interfaces import MessageProcessor
from ..processors.telemetry_processor import TelemetryMessageProcessor


class MessageProcessorFactory:
    """Factory for creating message processor instances."""

    @staticmethod
    def create_processor(processor_type: str, **kwargs) -> MessageProcessor:
        """Create a message processor instance.

        Args:
            processor_type: Type of processor to create
            **kwargs: Additional arguments for processor configuration

        Returns:
            MessageProcessor instance

        Raises:
            ValueError: If processor type is not supported
        """
        if processor_type == "telemetry":
            return TelemetryMessageProcessor()
        else:
            raise ValueError(f"Unsupported processor type: {processor_type}")
