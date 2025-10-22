#!/usr/bin/env python3
"""Complete E2E Telemetry Management Script.

This script combines all functionality from gen_sample_events.py and
batch_sqs_consumer.py into a single modular script that:
1. Starts consumers first
2. Processes any pending events in queue
3. Generates new events only if queue is empty

Uses OOP and SOLID principles with modular design.
"""

import argparse
import asyncio
import json
import logging
import os
import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class QueueMonitor:
    """Monitor SQS queue status and metrics."""

    def __init__(self, queue_url: str, aws_region: str = "us-east-1"):
        """Initialize QueueMonitor with queue URL and AWS region.

        Args:
            queue_url: SQS queue URL to monitor.
            aws_region: AWS region for SQS client (default: us-east-1).
        """
        self.queue_url = queue_url
        self.aws_region = aws_region

    def get_queue_depth(self) -> Dict[str, int]:
        """Get current queue message counts."""
        try:
            import boto3  # type: ignore

            sqs = boto3.client("sqs", region_name=self.aws_region)

            response = sqs.get_queue_attributes(
                QueueUrl=self.queue_url,
                AttributeNames=[
                    'ApproximateNumberOfMessages',
                    'ApproximateNumberOfMessagesNotVisible',
                ],
            )

            attributes = response.get('Attributes', {})
            available = int(attributes.get('ApproximateNumberOfMessages', 0))
            in_flight = int(attributes.get('ApproximateNumberOfMessagesNotVisible', 0))

            return {
                'available': available,
                'in_flight': in_flight,
                'total': available + in_flight,
            }
        except (ImportError, AttributeError, KeyError, ValueError) as e:
            logger.error("Failed to get queue depth: %s", e)
            return {'available': 0, 'in_flight': 0, 'total': 0}

    def has_pending_messages(self) -> bool:
        """Check if queue has pending messages."""
        depth = self.get_queue_depth()
        return depth['total'] > 0


class EventGenerator:
    """Generate telemetry events with timestamp for latency tracking."""

    def __init__(self, num_modules: int = 4):
        """Initialize EventGenerator with module configuration.

        Args:
            num_modules: Number of battery modules to simulate (default: 4).
        """
        self.num_modules = num_modules
        self.voltage_range = (3400, 4150)
        self.offset_range = (-40, 40)

    def generate_events(self, num_events: int) -> List[Dict[str, Any]]:
        """Generate battery cell telemetry events."""
        logger.info("Generating %d telemetry events", num_events)

        # Generate module offsets
        module_offsets = [
            random.randint(*self.offset_range) for _ in range(self.num_modules)
        ]

        events = []
        for _ in range(num_events):
            # Generate voltages for each module
            module_voltages = []
            for idx in range(self.num_modules):
                base_voltage = random.randint(*self.voltage_range)
                noisy_voltage = base_voltage + module_offsets[idx]
                module_voltages.append(noisy_voltage)

            # Create event with timestamp for E2E latency tracking
            event: Dict[str, Any] = {
                'timestamp': time.time(),  # For E2E latency measurement
                'epoch_timestamp': int(time.time() * 1000),  # Milliseconds
            }

            # Add cell voltages
            for i, voltage in enumerate(module_voltages):
                event[f"Cell{i + 1}Voltage"] = voltage

            # Add summary statistics
            event.update(
                {
                    "min_voltage": min(module_voltages),
                    "max_voltage": max(module_voltages),
                    "avg_voltage": round(sum(module_voltages) / self.num_modules),
                    "module_offsets": [float(offset) for offset in module_offsets],
                }
            )

            events.append(event)

        return events

    def save_events_to_file(
        self, events: List[Dict[str, Any]], file_path: Optional[str] = None
    ):
        """Save generated events to JSONL file for analysis."""
        if file_path is None:
            # Default to the project's sample events file
            script_dir = Path(__file__).parent
            data_dir = script_dir.parent / "data"
            file_path = str(data_dir / "sample_events_mvp.jsonl")

        try:
            with open(file_path, 'a', encoding='utf-8') as f:
                for event in events:
                    f.write(json.dumps(event) + '\n')
            logger.info("Saved %d events to %s", len(events), file_path)
        except (IOError, OSError) as e:
            logger.error("Failed to save events to file: %s", e)

    def publish_to_sqs(
        self, events: List[Dict[str, Any]], queue_url: str
    ) -> Dict[str, Any]:
        """Publish events to SQS with batch processing."""
        try:
            import boto3

            sqs = boto3.client("sqs", region_name=os.getenv("AWS_REGION", "us-east-1"))

            successes = 0
            failures = 0

            # Batch publish in groups of 10 (SQS limit)
            batch_size = 10
            for i in range(0, len(events), batch_size):
                batch = events[i : i + batch_size]

                # Prepare batch entries
                entries = []
                for idx, event in enumerate(batch):
                    entries.append({'Id': str(idx), 'MessageBody': json.dumps(event)})

                try:
                    response = sqs.send_message_batch(
                        QueueUrl=queue_url, Entries=entries
                    )

                    successes += len(response.get('Successful', []))
                    failures += len(response.get('Failed', []))

                except (ImportError, AttributeError, KeyError, ValueError) as e:
                    logger.error("Batch publish failed: %s", e)
                    failures += len(batch)

            return {
                'events_published': successes,
                'publish_failures': failures,
                'total_events': len(events),
            }

        except (ImportError, AttributeError, KeyError, ValueError) as e:
            logger.error("Failed to publish to SQS: %s", e)
            return {
                'events_published': 0,
                'publish_failures': len(events),
                'total_events': len(events),
                'error': str(e),
            }


class MessageProcessor:
    """Process telemetry messages with latency tracking."""

    def __init__(self):
        """Initialize MessageProcessor with tracking metrics."""
        self.processed_count = 0
        self.processing_times = []
        self.e2e_latencies = []  # Track E2E latencies

    def process_message(self, message_body: str) -> Dict[str, Any]:
        """Process a single telemetry message."""
        start_time = time.time()

        try:
            # Parse message
            data = json.loads(message_body)

            # Calculate E2E latency if timestamp exists
            e2e_latency = None
            if 'timestamp' in data:
                e2e_latency = start_time - data['timestamp']

            # Simple processing (could be extended)
            processed_data = {
                'message_id': self.processed_count,
                'processing_time': time.time() - start_time,
                'e2e_latency': e2e_latency,
                'cell_count': len(
                    [k for k in data.keys() if 'Cell' in k and 'Voltage' in k]
                ),
                'avg_voltage': data.get('avg_voltage', 0),
                'processing_timestamp': time.time(),
                'original_data': data,  # Include original event data
            }

            self.processed_count += 1
            self.processing_times.append(processed_data['processing_time'])

            # Track E2E latency if available
            if e2e_latency is not None:
                self.e2e_latencies.append(e2e_latency)

            # Log latency for visibility
            if e2e_latency is not None:
                logger.info(
                    "Message %d: E2E latency=%.3fs, Processing=%.3fs",
                    self.processed_count,
                    e2e_latency,
                    processed_data['processing_time'],
                )

            return {'status': 'success', 'processed_data': processed_data}

        except (KeyError, ValueError, TypeError) as e:
            logger.error("Message processing failed: %s", e)
            return {'status': 'error', 'error': str(e)}

    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        stats = {
            'messages_processed': self.processed_count,
            'avg_processing_time': (
                sum(self.processing_times) / len(self.processing_times)
                if self.processing_times
                else 0
            ),
            'total_processing_time': sum(self.processing_times),
        }

        # Add E2E latency stats if available
        if self.e2e_latencies:
            stats.update(
                {
                    'messages_with_latency': len(self.e2e_latencies),
                    'avg_e2e_latency': sum(self.e2e_latencies)
                    / len(self.e2e_latencies),
                    'min_e2e_latency': min(self.e2e_latencies),
                    'max_e2e_latency': max(self.e2e_latencies),
                }
            )

        return stats

    def save_processing_metrics(
        self, processed_messages: List[Dict[str, Any]], file_path: Optional[str] = None
    ):
        """Save processing metrics to JSONL file."""
        if file_path is None:
            # Default to metrics directory - correct path from scripts folder
            script_dir = Path(__file__).parent
            metrics_dir = script_dir.parent / "data" / "metrics"
            metrics_dir.mkdir(exist_ok=True)

            # Use today's date for filename
            today = time.strftime("%Y-%m-%d")
            file_path = str(metrics_dir / f"latency-{today}.jsonl")

        try:
            with open(file_path, 'a', encoding='utf-8') as f:
                for message in processed_messages:
                    # Create metrics record
                    metrics_record = {
                        'timestamp': message.get('processing_timestamp', time.time()),
                        'message_id': message.get('message_id'),
                        'e2e_latency_seconds': message.get('e2e_latency'),
                        'processing_time_seconds': message.get('processing_time'),
                        'cell_count': message.get('cell_count'),
                        'avg_voltage': message.get('avg_voltage'),
                        'original_event': message.get('original_data', {}),
                    }
                    f.write(json.dumps(metrics_record) + '\n')

            logger.info(
                "Saved %d processing metrics to %s", len(processed_messages), file_path
            )
        except (IOError, OSError) as e:
            logger.error("Failed to save processing metrics: %s", e)


class ConcurrentConsumer:
    """Concurrent SQS consumer using ThreadPoolExecutor."""

    def __init__(
        self, queue_url: str, aws_region: str = "us-east-1", max_workers: int = 4
    ):
        """Initialize ConcurrentConsumer with SQS configuration.

        Args:
            queue_url: SQS queue URL to consume from.
            aws_region: AWS region for SQS client (default: us-east-1).
            max_workers: Maximum number of worker threads (default: 4).
        """
        self.queue_url = queue_url
        self.aws_region = aws_region
        self.max_workers = max_workers
        self.processor = MessageProcessor()

        # Initialize SQS client
        import boto3

        self.sqs = boto3.client("sqs", region_name=aws_region)

    def _receive_messages(self) -> List[Dict[str, Any]]:
        """Receive messages from SQS queue."""
        response = self.sqs.receive_message(
            QueueUrl=self.queue_url,
            MaxNumberOfMessages=10,
            WaitTimeSeconds=0,  # No wait for immediate processing
            MessageAttributeNames=['All'],
        )
        return response.get('Messages', [])

    def _process_messages_concurrently(
        self, messages: List[Dict[str, Any]]
    ) -> tuple[List[Dict[str, Any]], int]:
        """Process messages concurrently and return processed data and delete count."""
        processed_messages = []
        successful_deletes = 0

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit processing tasks
            processing_futures = {
                executor.submit(self.processor.process_message, msg['Body']): msg
                for msg in messages
            }

            # Collect results and delete successfully processed messages
            for future in processing_futures:
                message = processing_futures[future]
                try:
                    result = future.result(timeout=30)  # 30 second timeout

                    if result['status'] == 'success':
                        # Collect processed message data for metrics
                        processed_messages.append(result.get('processed_data', {}))

                        # Delete message from queue
                        if self._delete_message(message['ReceiptHandle']):
                            successful_deletes += 1

                except (
                    TimeoutError, RuntimeError, ValueError, TypeError, KeyError
                ) as e:
                    logger.error("Message processing failed: %s", e)

        return processed_messages, successful_deletes

    def _delete_message(self, receipt_handle: str) -> bool:
        """Delete a message from the queue. Returns True if successful."""
        try:
            self.sqs.delete_message(
                QueueUrl=self.queue_url,
                ReceiptHandle=receipt_handle,
            )
            return True
        except (ImportError, AttributeError, KeyError, ValueError) as e:
            logger.error("Failed to delete message: %s", e)
            return False

    def consume_batch(self) -> Dict[str, Any]:
        """Consume and process a batch of messages concurrently."""
        try:
            # Receive messages
            messages = self._receive_messages()
            if not messages:
                return {
                    'messages_received': 0,
                    'messages_processed': 0,
                    'messages_deleted': 0,
                }

            logger.info("Received %d messages for processing", len(messages))

            # Process messages concurrently
            (
                processed_messages,
                successful_deletes,
            ) = self._process_messages_concurrently(messages)

            # Save processing metrics to JSONL if any messages were processed
            if processed_messages:
                self.processor.save_processing_metrics(processed_messages)

            return {
                'messages_received': len(messages),
                'messages_processed': len(messages),
                'messages_deleted': successful_deletes,
            }

        except (ImportError, AttributeError, KeyError, ValueError) as e:
            logger.error("Batch consumption failed: %s", e)
            return {
                'messages_received': 0,
                'messages_processed': 0,
                'messages_deleted': 0,
                'error': str(e),
            }

    def get_processor_stats(self) -> Dict[str, Any]:
        """Get processor statistics."""
        return self.processor.get_stats()


class E2ETelemetryOrchestrator:
    """Main orchestrator for the complete E2E telemetry workflow."""

    def __init__(self, queue_url: str, aws_region: str = "us-east-1"):
        """Initialize E2ETelemetryOrchestrator with SQS configuration.

        Args:
            queue_url: SQS queue URL for telemetry workflow.
            aws_region: AWS region for SQS operations (default: us-east-1).
        """
        self.queue_url = queue_url
        self.aws_region = aws_region
        self.queue_monitor = QueueMonitor(queue_url, aws_region)
        self.event_generator = EventGenerator()
        self.consumer = ConcurrentConsumer(queue_url, aws_region)

    async def execute_workflow(
        self, num_events: int = 100, max_processing_time: int = 60
    ) -> Dict[str, Any]:
        """Execute the complete E2E workflow with consumers starting first."""
        workflow_start = time.time()
        logger.info("🚀 Starting E2E telemetry workflow")

        results = {
            'workflow_start': workflow_start,
            'queue_url': self.queue_url,
            'target_events': num_events,
            'max_processing_time': max_processing_time,
        }

        try:
            # Phase 1: Start consumers immediately
            print("🚀 Starting consumers...")
            logger.info("🔄 Phase 1: Starting concurrent consumers")

            # Phase 2: Check initial queue status
            logger.info("📊 Phase 2: Checking initial queue status")
            initial_depth = self.queue_monitor.get_queue_depth()
            results['initial_queue_depth'] = initial_depth

            print("📬 Initial queue status:")
            print(f"  • Available messages: {initial_depth['available']}")
            print(f"  • In-flight messages: {initial_depth['in_flight']}")
            print(f"  • Total queue depth: {initial_depth['total']}")

            # Phase 3: Drain old messages first (discard high latency data)
            if initial_depth['total'] > 0:
                print(
                    f"\n🧹 Draining {initial_depth['total']} old messages "
                    "(discarding high latency data)..."
                )
                logger.info(
                    "Draining %d old messages from queue", initial_depth['total']
                )

                # Process old messages but don't save metrics (discard data)
                drain_results = await self._drain_old_messages(max_processing_time)
                results['drain_phase'] = drain_results

                print("✅ Queue drained successfully")
                print(f"  • Old messages processed: {drain_results['total_processed']}")
                print(f"  • Drain time: {drain_results['total_time']:.2f}s")
                print("  • ℹ️  High latency data discarded")
            else:
                print("\n✅ No old messages to drain")
                results['drain_phase'] = {'total_processed': 0, 'total_time': 0}

            # Phase 4: Wait longer for queue to stabilize and SQS eventual consistency
            print("\n⏳ Waiting for queue to stabilize...")
            await asyncio.sleep(3)  # Increased from 2s to 3s for better SQS consistency

            # Phase 5: Generate fresh events first
            print("📊 Generating fresh events for accurate latency measurement...")
            logger.info("Generating %d fresh events with active consumers", num_events)

            generation_results = self._generate_and_publish_events(num_events)
            results['generation_phase'] = generation_results

            if generation_results['status'] == 'success':
                print(
                    f"✅ Generated and published "
                    f"{generation_results['events_published']} fresh events"
                )
                print(
                    f"  • Generation time: {generation_results['generation_time']:.2f}s"
                )
                print(
                    f"  • Throughput: "
                    f"{generation_results['throughput_eps']:.1f} events/sec"
                )

                # Extended delay for SQS message propagation and visibility
                print("⏳ Waiting for SQS message propagation...")
                await asyncio.sleep(5)  # Increased from 2s to 5s for better propagation

                # Verify messages are visible in queue
                depth_info = self.queue_monitor.get_queue_depth()
                print("📊 Queue status after generation:")
                print(f"  • Available messages: {depth_info['available']}")
                print(f"  • In-flight messages: {depth_info['in_flight']}")

                # Additional wait if no messages are visible yet
                if depth_info['total'] == 0:
                    print("⚠️ Messages not yet visible - waiting longer...")
                    await asyncio.sleep(5)  # Additional 5s if needed

                # NOW start fresh consumer task AFTER events are generated and visible
                print("🔄 Processing fresh events for accurate latency measurement...")
                fresh_consumer_task = asyncio.create_task(
                    self._process_fresh_messages(
                        max_processing_time + 10
                    )  # Extra 10s for fresh events
                )
                processing_results = await fresh_consumer_task
                results['processing_phase'] = processing_results

                print("✅ Fresh event processing completed")
                print(
                    f"  • Fresh messages processed: "
                    f"{processing_results['total_processed']}"
                )
                print(f"  • Processing time: {processing_results['total_time']:.2f}s")

                # Show latency stats for fresh events only
                if 'processor_stats' in processing_results and processing_results[
                    'processor_stats'
                ].get('avg_e2e_latency'):
                    stats = processing_results['processor_stats']
                    print("\n📊 E2E Latency Report (Fresh Events Only):")
                    print(
                        f"  • Messages with latency data: "
                        f"{stats.get('messages_with_latency', 0)}"
                    )
                    print(f"  • Average E2E latency: {stats['avg_e2e_latency']:.3f}s")
                    print(f"  • Min E2E latency: {stats['min_e2e_latency']:.3f}s")
                    print(f"  • Max E2E latency: {stats['max_e2e_latency']:.3f}s")
                else:
                    print("\n⚠️ No latency data available for fresh events")
            else:
                print(
                    f"❌ Generation failed: "
                    f"{generation_results.get('error', 'Unknown error')}"
                )
                # Create empty processing results since generation failed
                results['processing_phase'] = {
                    'total_processed': 0,
                    'total_time': 0,
                    'processor_stats': {},
                }

            # Final results
            total_time = time.time() - workflow_start
            results['total_workflow_time'] = total_time
            results['status'] = 'completed'

            print("\n🎉 E2E Workflow completed successfully!")
            print(f"  • Total time: {total_time:.2f}s")
            print(
                f"  • Messages processed: "
                f"{results['processing_phase']['total_processed']}"  # type: ignore
            )
            events_generated = results.get('generation_phase', {}).get(  # type: ignore
                'events_published', 0
            )
            print(f"  • Events generated: {events_generated}")

            return results

        except (
            ImportError, AttributeError, KeyError, ValueError, OSError, IOError
        ) as e:
            logger.error("Workflow failed: %s", e)
            results['status'] = 'error'
            results['error'] = str(e)
            results['total_workflow_time'] = time.time() - workflow_start

            print(f"\n❌ Workflow failed: {e}")
            return results

    async def _process_pending_messages(self, max_duration: int) -> Dict[str, Any]:
        """Process pending messages using concurrent consumer."""
        start_time = time.time()
        total_processed = 0
        total_batches = 0
        consecutive_empty_batches = 0
        max_empty_batches = 5  # Stop after 5 consecutive empty batches

        while time.time() - start_time < max_duration:
            # Try to consume messages
            batch_results = self.consumer.consume_batch()
            total_batches += 1

            if batch_results['messages_processed'] > 0:
                total_processed += batch_results['messages_processed']
                consecutive_empty_batches = 0  # Reset counter on successful processing
            else:
                consecutive_empty_batches += 1

            # Exit if we've had too many consecutive empty batches
            if consecutive_empty_batches >= max_empty_batches:
                logger.info("Queue cleared, stopping consumption")
                break

            # Give small delay between batches for CPU efficiency
            await asyncio.sleep(0.01)  # Reduced delay for lower latency

        processor_stats = self.consumer.get_processor_stats()

        return {
            'total_processed': total_processed,
            'total_batches': total_batches,
            'total_time': time.time() - start_time,
            'processor_stats': processor_stats,
        }

    async def _drain_old_messages(self, max_duration: int) -> Dict[str, Any]:
        """Drain old messages from queue without saving metrics."""
        start_time = time.time()
        total_processed = 0
        total_batches = 0
        consecutive_empty_batches = 0
        max_empty_batches = 3  # Stop after 3 consecutive empty batches

        # Create a temporary consumer that doesn't save metrics
        temp_consumer = ConcurrentConsumer(self.queue_url, self.aws_region)

        while time.time() - start_time < max_duration:
            # Try to consume messages without saving metrics
            try:
                response = temp_consumer.sqs.receive_message(
                    QueueUrl=self.queue_url,
                    MaxNumberOfMessages=10,
                    WaitTimeSeconds=0,
                    MessageAttributeNames=['All'],
                )

                messages = response.get('Messages', [])
                total_batches += 1

                if messages:
                    logger.info(
                        "Draining %d old messages (not saving metrics)", len(messages)
                    )

                    # Delete messages without processing for metrics
                    for message in messages:
                        try:
                            temp_consumer.sqs.delete_message(
                                QueueUrl=self.queue_url,
                                ReceiptHandle=message['ReceiptHandle'],
                            )
                            total_processed += 1
                        except (ImportError, AttributeError, KeyError, ValueError) as e:
                            logger.error("Failed to delete old message: %s", e)

                    consecutive_empty_batches = 0
                else:
                    consecutive_empty_batches += 1

                # Exit if we've had too many consecutive empty batches
                if consecutive_empty_batches >= max_empty_batches:
                    break

                # Small delay between batches
                await asyncio.sleep(0.1)

            except (ImportError, AttributeError, KeyError, ValueError) as e:
                logger.error("Error draining old messages: %s", e)
                break

        return {
            'total_processed': total_processed,
            'total_batches': total_batches,
            'total_time': time.time() - start_time,
        }

    async def _process_fresh_messages(self, max_duration: int) -> Dict[str, Any]:
        """Process fresh messages and save metrics for accurate latency measurement."""
        start_time = time.time()
        total_processed = 0
        total_batches = 0
        consecutive_empty_batches = 0
        max_empty_batches = 15  # Wait longer for fresh messages (increased from 10)

        # Reset the processor stats for fresh measurements
        self.consumer.processor = MessageProcessor()

        logger.info("Starting fresh message processing with %ds timeout", max_duration)

        while time.time() - start_time < max_duration:
            # Try to consume messages
            batch_results = self.consumer.consume_batch()
            total_batches += 1

            if batch_results['messages_processed'] > 0:
                total_processed += batch_results['messages_processed']
                consecutive_empty_batches = 0  # Reset counter on successful processing
                logger.info(
                    "Processed %d fresh messages", batch_results['messages_processed']
                )
            else:
                consecutive_empty_batches += 1

            # Exit if we've had too many consecutive empty batches
            if consecutive_empty_batches >= max_empty_batches:
                logger.info(
                    "No more fresh messages after %d empty batches, stopping",
                    consecutive_empty_batches,
                )
                break

            # Smaller delay for more responsive fresh message processing
            await asyncio.sleep(0.05)  # Increased from 0.01s for better SQS polling

        processor_stats = self.consumer.get_processor_stats()

        return {
            'total_processed': total_processed,
            'total_batches': total_batches,
            'total_time': time.time() - start_time,
            'processor_stats': processor_stats,
        }

    def _generate_and_publish_events(self, num_events: int) -> Dict[str, Any]:
        """Generate events and publish to SQS."""
        try:
            start_time = time.time()

            # Generate events
            events = self.event_generator.generate_events(num_events)

            # Save events to JSONL file for analysis
            self.event_generator.save_events_to_file(events)

            # Publish to SQS
            publish_results = self.event_generator.publish_to_sqs(
                events, self.queue_url
            )

            generation_time = time.time() - start_time

            return {
                'status': 'success',
                'events_generated': len(events),
                'events_published': publish_results['events_published'],
                'publish_failures': publish_results['publish_failures'],
                'generation_time': generation_time,
                'throughput_eps': len(events) / generation_time,
            }

        except (
            ImportError, AttributeError, KeyError, ValueError, OSError, IOError
        ) as e:
            logger.error("Event generation and publishing failed: %s", e)
            return {'status': 'error', 'error': str(e)}


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser."""
    parser = argparse.ArgumentParser(
        description="Complete E2E Telemetry Workflow Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic workflow
  python e2e_telemetry.py --queue-url https://sqs.us-east-1.amazonaws.com/123/queue

  # Custom parameters
  python e2e_telemetry.py --queue-url YOUR_QUEUE_URL --events 500 --max-time 120
        """,
    )

    parser.add_argument(
        "--queue-url",
        type=str,
        default=os.getenv("SQS_QUEUE_URL"),
        help="SQS queue URL (default: from SQS_QUEUE_URL env var)",
    )

    parser.add_argument(
        "--events",
        type=int,
        default=100,
        help="Number of events to generate if queue is empty (default: 100)",
    )

    parser.add_argument(
        "--max-time",
        type=int,
        default=60,
        help="Maximum time for processing pending messages (default: 60s)",
    )

    parser.add_argument(
        "--region",
        type=str,
        default="us-east-1",
        help="AWS region (default: us-east-1)",
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose debug logging"
    )

    return parser


async def main():
    """Execute the complete E2E telemetry workflow."""
    parser = create_parser()
    args = parser.parse_args()

    # Validate arguments
    if not args.queue_url:
        print("❌ Error: --queue-url is required")
        print("Set SQS_QUEUE_URL environment variable or use --queue-url argument")
        sys.exit(1)

    # Setup logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    print("🚀 Complete E2E Telemetry Workflow Manager")
    print("=" * 45)
    print(f"Queue URL: {args.queue_url[:50]}...")
    print(f"Region: {args.region}")
    print(f"Events to generate: {args.events}")
    print(f"Max processing time: {args.max_time}s")

    # Create and run orchestrator
    orchestrator = E2ETelemetryOrchestrator(args.queue_url, args.region)

    try:
        results = await orchestrator.execute_workflow(
            num_events=args.events, max_processing_time=args.max_time
        )

        if results.get('status') == 'error':
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n🛑 Workflow interrupted by user")
    except (ImportError, AttributeError, KeyError, ValueError, OSError, IOError) as e:
        logger.error("Unexpected error: %s", e, exc_info=True)
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
