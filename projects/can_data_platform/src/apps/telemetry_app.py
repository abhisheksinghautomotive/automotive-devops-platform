"""Telemetry application orchestrator using Dependency Injection pattern."""

import logging
import time
from typing import List, Dict, Any, Optional

from ..config import TelemetryConfig
from ..events import EventGenerator
from ..file_operations import FileWriter
from ..publishers import PublisherInterface
from ..tracking import ProgressTracker


logger = logging.getLogger(__name__)


class TelemetryApp:
    """Main application class following Dependency Injection pattern.

    Orchestrates event generation, publishing, and file operations.
    Follows Open/Closed Principle - extensible without modification.
    """

    def __init__(
        self,
        config: TelemetryConfig,
        event_generator: EventGenerator,
        file_writer: FileWriter,
        publisher: PublisherInterface,
        progress_tracker: ProgressTracker,
    ):
        """Initialize telemetry application with dependencies.

        Args:
            config: Application configuration
            event_generator: Event generator implementation
            file_writer: File writer implementation
            publisher: Publisher implementation
            progress_tracker: Progress tracker implementation
        """
        self.config = config
        self.event_generator = event_generator
        self.file_writer = file_writer
        self.publisher = publisher
        self.progress_tracker = progress_tracker

    def generate_events(self, num_events: int) -> List[Dict[str, Any]]:
        """Generate telemetry events with progress tracking.

        Args:
            num_events: Number of events to generate

        Returns:
            List of event dictionaries
        """
        logger.info("Generating %d telemetry events", num_events)

        self.progress_tracker.start(num_events, "⚡ Generating Events")

        start_time = time.time()

        # Generate events using the injected generator
        events_objects = self.event_generator.generate_events(num_events)

        # Convert to dictionaries for serialization
        events = []
        for event_obj in events_objects:
            events.append(event_obj.to_dict())
            self.progress_tracker.update(1)

        generation_time = time.time() - start_time
        self.progress_tracker.close()

        logger.info(
            "Event generation completed in %.2fs (%.1f events/sec)",
            generation_time,
            num_events / generation_time,
        )

        return events

    def publish_to_file(self, events: List[Dict[str, Any]], output_path: str) -> None:
        """Publish events to file.

        Args:
            events: List of event dictionaries
            output_path: Output file path
        """
        logger.info("Writing %d events to file: %s", len(events), output_path)

        try:
            self.file_writer.write(events, output_path)
            print(f"✅ Wrote {len(events)} events to {output_path}")

        except (OSError, IOError) as e:
            logger.error("Failed to write events to file: %s", e)
            print(f"❌ Failed to write events to file: {e}")
            raise

    def publish_to_sqs(self, events: List[Dict[str, Any]]) -> Dict[str, int]:
        """Publish events to SQS with progress tracking.

        Args:
            events: List of event dictionaries

        Returns:
            Publishing statistics
        """
        logger.info("Publishing %d events to SQS", len(events))

        # Setup progress tracking for SQS publishing
        self.progress_tracker.start(len(events), "📡 Publishing to SQS")

        start_time = time.time()

        try:
            # Use the injected publisher with progress tracker
            result = self.publisher.publish(events, self.progress_tracker)

            publishing_time = time.time() - start_time

            # Final progress update
            self.progress_tracker.set_postfix(
                {
                    "✅": result.successes,
                    "❌": result.failures,
                    "📦": result.batches,
                    "🔄": result.retries,
                    "📊": f"{result.success_rate:.1f}%",
                }
            )
            self.progress_tracker.close()

            logger.info(
                "SQS publishing completed in %.2fs (%.1f events/sec)",
                publishing_time,
                result.successes / publishing_time if result.successes > 0 else 0,
            )

            # Print results
            print("🎯 SQS Batch Publishing Results:")
            print(f"   ✅ Successful Events: {result.successes}")
            print(f"   ❌ Failed Events: {result.failures}")
            print(f"   📦 Batches Sent: {result.batches}")
            print(f"   🔄 Total Retries: {result.retries}")
            print(f"   📊 Success Rate: {result.success_rate:.1f}%")

            return {
                "successes": result.successes,
                "failures": result.failures,
                "batches": result.batches,
                "retries": result.retries,
            }

        except Exception as e:
            self.progress_tracker.close()
            logger.error("SQS publishing failed: %s", e)
            print(f"❌ SQS publishing failed: {e}")
            raise

    def run(
        self, num_events: int, mode: str, output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Run the telemetry application.

        Args:
            num_events: Number of events to generate
            mode: Output mode ('file', 'sqs', or 'both')
            output_path: Output file path (for file mode)

        Returns:
            Execution statistics
        """
        logger.info("Starting telemetry application")
        logger.info("Mode: %s, Events: %d", mode, num_events)

        results: Dict[str, Any] = {}

        try:
            # Generate events
            start_time = time.time()
            events = self.generate_events(num_events)

            # Publish to file if requested
            if mode in ("file", "both"):
                file_path = output_path or self.config.default_output_path
                self.publish_to_file(events, file_path)
                results["file_written"] = True

            # Publish to SQS if requested
            if mode in ("sqs", "both"):
                if not self.config.sqs_queue_url:
                    raise ValueError("SQS_QUEUE_URL is required for SQS publishing")

                sqs_stats = self.publish_to_sqs(events)
                for key, value in sqs_stats.items():
                    results[key] = value

            total_time = time.time() - start_time
            results["total_execution_time"] = total_time

            logger.info("Total execution time: %.2fs", total_time)

            return results

        except Exception as e:
            logger.error("Application execution failed: %s", e)
            raise

        finally:
            # Cleanup resources
            try:
                self.publisher.close()
            except (AttributeError, OSError, IOError):
                pass  # Ignore cleanup errors
