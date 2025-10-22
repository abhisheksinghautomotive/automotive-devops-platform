#!/usr/bin/env python3
"""
Unit tests for E2E Telemetry Management Script

Tests all classes and methods in e2e_telemetry.py including:
- QueueMonitor: SQS queue monitoring
- EventGenerator: Event generation and publishing
- MessageProcessor: Message processing logic
- ConcurrentConsumer: Concurrent SQS message consumption
- E2ETelemetryOrchestrator: Main workflow orchestration
"""

import argparse
import json
import logging
import unittest
from unittest.mock import Mock, patch

# Import the module under test
import projects.can_data_platform.scripts.e2e_telemetry as e2e_telemetry


class TestQueueMonitor(unittest.TestCase):
    """Test QueueMonitor class for SQS queue monitoring."""

    def setUp(self):
        """Set up test fixtures."""
        self.queue_url = "https://sqs.us-east-1.amazonaws.com/123456789/test-queue"
        self.monitor = e2e_telemetry.QueueMonitor(
            queue_url=self.queue_url, aws_region="us-east-1"
        )

    @patch('boto3.client')
    def test_get_queue_depth_success(self, mock_boto_client):
        """Test successful queue depth retrieval."""
        # Arrange
        mock_sqs = Mock()
        mock_boto_client.return_value = mock_sqs
        mock_sqs.get_queue_attributes.return_value = {
            'Attributes': {
                'ApproximateNumberOfMessages': '5',
                'ApproximateNumberOfMessagesNotVisible': '2',
            }
        }

        # Act
        result = self.monitor.get_queue_depth()

        # Assert
        expected = {'available': 5, 'in_flight': 2, 'total': 7}
        self.assertEqual(result, expected)
        mock_boto_client.assert_called_once_with("sqs", region_name="us-east-1")
        mock_sqs.get_queue_attributes.assert_called_once()

    @patch('boto3.client')
    def test_get_queue_depth_boto_error(self, mock_boto_client):
        """Test queue depth retrieval with boto error."""
        # Arrange
        mock_sqs = Mock()
        mock_boto_client.return_value = mock_sqs
        mock_sqs.get_queue_attributes.side_effect = Exception("Connection error")

        # Act
        result = self.monitor.get_queue_depth()

        # Assert
        expected = {'available': 0, 'in_flight': 0, 'total': 0}
        self.assertEqual(result, expected)

    def test_queue_monitor_initialization(self):
        """Test QueueMonitor proper initialization."""
        # Act & Assert
        self.assertEqual(self.monitor.queue_url, self.queue_url)
        self.assertEqual(self.monitor.aws_region, "us-east-1")

    def test_queue_monitor_default_region(self):
        """Test QueueMonitor with default region."""
        # Act
        monitor = e2e_telemetry.QueueMonitor(queue_url=self.queue_url)

        # Assert
        self.assertEqual(monitor.aws_region, "us-east-1")


class TestEventGenerator(unittest.TestCase):
    """Test EventGenerator class for event generation and publishing."""

    def setUp(self):
        """Set up test fixtures."""
        self.generator = e2e_telemetry.EventGenerator(num_modules=4)

    def test_event_generator_initialization(self):
        """Test EventGenerator proper initialization."""
        # Act & Assert
        self.assertEqual(self.generator.num_modules, 4)
        self.assertEqual(self.generator.voltage_range, (3400, 4150))
        self.assertEqual(self.generator.offset_range, (-40, 40))

    def test_event_generator_default_modules(self):
        """Test EventGenerator with default number of modules."""
        # Act
        generator = e2e_telemetry.EventGenerator()

        # Assert
        self.assertEqual(generator.num_modules, 4)

    @patch('random.randint')
    @patch('time.time')
    def test_generate_events(self, mock_time, mock_randint):
        """Test event generation with mocked random values."""
        # Arrange
        mock_time.return_value = 1640995200.0  # Fixed timestamp
        mock_randint.side_effect = [
            10,
            20,
            30,
            40,  # module offsets
            3500,
            3600,
            3700,
            3800,
        ]  # voltages

        # Act
        events = self.generator.generate_events(num_events=1)

        # Assert
        self.assertEqual(len(events), 1)
        event = events[0]
        self.assertEqual(event['timestamp'], 1640995200.0)
        self.assertEqual(event['epoch_timestamp'], 1640995200000)
        self.assertIn('Cell1Voltage', event)
        self.assertIn('Cell2Voltage', event)
        self.assertIn('Cell3Voltage', event)
        self.assertIn('Cell4Voltage', event)
        self.assertIn('min_voltage', event)
        self.assertIn('max_voltage', event)
        self.assertIn('avg_voltage', event)

    @patch('builtins.open', create=True)
    def test_save_events_to_file(self, mock_open):
        """Test saving events to file."""
        # Arrange
        mock_file = Mock()
        mock_open.return_value.__enter__.return_value = mock_file

        events = [{'test': 'event1'}, {'test': 'event2'}]

        # Act
        self.generator.save_events_to_file(events, '/tmp/test.jsonl')

        # Assert
        mock_open.assert_called_once_with('/tmp/test.jsonl', 'a')
        self.assertEqual(mock_file.write.call_count, 2)

    @patch('boto3.client')
    def test_publish_to_sqs_success(self, mock_boto_client):
        """Test successful SQS message publishing."""
        # Arrange
        mock_sqs = Mock()
        mock_boto_client.return_value = mock_sqs
        mock_sqs.send_message_batch.return_value = {
            'Successful': [{'Id': '0'}, {'Id': '1'}],
            'Failed': [],
        }

        events = [{'test': 'event1'}, {'test': 'event2'}]
        queue_url = "https://sqs.us-east-1.amazonaws.com/123456789/test-queue"

        # Act
        result = self.generator.publish_to_sqs(events, queue_url)

        # Assert
        self.assertEqual(result['events_published'], 2)
        self.assertEqual(result['publish_failures'], 0)
        self.assertEqual(result['total_events'], 2)

    @patch('boto3.client')
    def test_publish_to_sqs_with_failures(self, mock_boto_client):
        """Test SQS publishing with some failures."""
        # Arrange
        mock_sqs = Mock()
        mock_boto_client.return_value = mock_sqs
        mock_sqs.send_message_batch.return_value = {
            'Successful': [{'Id': '0'}],
            'Failed': [{'Id': '1'}],
        }

        events = [{'test': 'event1'}, {'test': 'event2'}]
        queue_url = "https://sqs.us-east-1.amazonaws.com/123456789/test-queue"

        # Act
        result = self.generator.publish_to_sqs(events, queue_url)

        # Assert
        self.assertEqual(result['events_published'], 1)
        self.assertEqual(result['publish_failures'], 1)
        self.assertEqual(result['total_events'], 2)


class TestMessageProcessor(unittest.TestCase):
    """Test MessageProcessor class for message processing logic."""

    def setUp(self):
        """Set up test fixtures."""
        self.processor = e2e_telemetry.MessageProcessor()

    def test_message_processor_initialization(self):
        """Test MessageProcessor proper initialization."""
        # Act & Assert
        self.assertEqual(self.processor.processed_count, 0)
        self.assertEqual(self.processor.processing_times, [])
        self.assertEqual(self.processor.e2e_latencies, [])

    def test_process_message_valid_json(self):
        """Test processing valid JSON message."""
        # Arrange
        message_body = json.dumps(
            {
                'timestamp': 1640995200.0,
                'Cell1Voltage': 3500,
                'Cell2Voltage': 3600,
                'avg_voltage': 3550,
            }
        )

        # Act
        result = self.processor.process_message(message_body)

        # Assert
        self.assertEqual(result['status'], 'success')
        self.assertIn('processed_data', result)
        processed_data = result['processed_data']
        self.assertEqual(processed_data['message_id'], 0)
        self.assertEqual(processed_data['cell_count'], 2)
        self.assertEqual(processed_data['avg_voltage'], 3550)
        self.assertIsNotNone(processed_data['e2e_latency'])

    def test_process_message_invalid_json(self):
        """Test processing invalid JSON message."""
        # Arrange
        message_body = "invalid json {{"

        # Act
        result = self.processor.process_message(message_body)

        # Assert
        self.assertEqual(result['status'], 'error')
        self.assertIn('error', result)

    def test_process_message_without_timestamp(self):
        """Test processing message without timestamp."""
        # Arrange
        message_body = json.dumps({'Cell1Voltage': 3500, 'avg_voltage': 3550})

        # Act
        result = self.processor.process_message(message_body)

        # Assert
        self.assertEqual(result['status'], 'success')
        processed_data = result['processed_data']
        self.assertIsNone(processed_data['e2e_latency'])

    def test_get_stats_empty(self):
        """Test getting stats when no messages processed."""
        # Act
        stats = self.processor.get_stats()

        # Assert
        expected = {
            'messages_processed': 0,
            'avg_processing_time': 0,
            'total_processing_time': 0,
        }
        self.assertEqual(stats, expected)

    def test_get_stats_with_data(self):
        """Test getting stats after processing messages."""
        # Arrange
        message_body = json.dumps({'timestamp': 1640995200.0, 'test': 'data'})
        self.processor.process_message(message_body)

        # Act
        stats = self.processor.get_stats()

        # Assert
        self.assertEqual(stats['messages_processed'], 1)
        self.assertGreater(stats['avg_processing_time'], 0)
        self.assertIn('messages_with_latency', stats)
        self.assertIn('avg_e2e_latency', stats)

    @patch('builtins.open', create=True)
    def test_save_processing_metrics(self, mock_open):
        """Test saving processing metrics to file."""
        # Arrange
        mock_file = Mock()
        mock_open.return_value.__enter__.return_value = mock_file

        processed_messages = [
            {
                'processing_timestamp': 1640995200.0,
                'message_id': 0,
                'e2e_latency': 0.1,
                'processing_time': 0.01,
                'cell_count': 2,
                'avg_voltage': 3550,
                'original_data': {'test': 'data'},
            }
        ]

        # Act
        self.processor.save_processing_metrics(processed_messages, '/tmp/test.jsonl')

        # Assert
        mock_open.assert_called_once_with('/tmp/test.jsonl', 'a')
        mock_file.write.assert_called_once()


class TestConcurrentConsumer(unittest.TestCase):
    """Test ConcurrentConsumer class for concurrent SQS message consumption."""

    def setUp(self):
        """Set up test fixtures."""
        self.queue_url = "https://sqs.us-east-1.amazonaws.com/123456789/test-queue"

    @patch('boto3.client')
    def test_concurrent_consumer_initialization(self, mock_boto_client):
        """Test ConcurrentConsumer proper initialization."""
        # Arrange
        mock_sqs = Mock()
        mock_boto_client.return_value = mock_sqs

        # Act
        consumer = e2e_telemetry.ConcurrentConsumer(
            queue_url=self.queue_url, aws_region="us-east-1", max_workers=2
        )

        # Assert
        self.assertEqual(consumer.queue_url, self.queue_url)
        self.assertEqual(consumer.aws_region, "us-east-1")
        self.assertEqual(consumer.max_workers, 2)
        self.assertIsInstance(consumer.processor, e2e_telemetry.MessageProcessor)

    @patch('boto3.client')
    def test_receive_messages_success(self, mock_boto_client):
        """Test successful message receiving."""
        # Arrange
        mock_sqs = Mock()
        mock_boto_client.return_value = mock_sqs
        mock_sqs.receive_message.return_value = {
            'Messages': [
                {'Body': '{"test": "message1"}', 'ReceiptHandle': 'handle1'},
                {'Body': '{"test": "message2"}', 'ReceiptHandle': 'handle2'},
            ]
        }

        consumer = e2e_telemetry.ConcurrentConsumer(queue_url=self.queue_url)

        # Act
        messages = consumer._receive_messages()

        # Assert
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]['Body'], '{"test": "message1"}')

    @patch('boto3.client')
    def test_receive_messages_no_messages(self, mock_boto_client):
        """Test receiving when no messages available."""
        # Arrange
        mock_sqs = Mock()
        mock_boto_client.return_value = mock_sqs
        mock_sqs.receive_message.return_value = {}

        consumer = e2e_telemetry.ConcurrentConsumer(queue_url=self.queue_url)

        # Act
        messages = consumer._receive_messages()

        # Assert
        self.assertEqual(len(messages), 0)

    @patch('boto3.client')
    def test_delete_message_success(self, mock_boto_client):
        """Test successful message deletion."""
        # Arrange
        mock_sqs = Mock()
        mock_boto_client.return_value = mock_sqs

        consumer = e2e_telemetry.ConcurrentConsumer(queue_url=self.queue_url)

        # Act
        result = consumer._delete_message("test-receipt-handle")

        # Assert
        self.assertTrue(result)
        mock_sqs.delete_message.assert_called_once_with(
            QueueUrl=self.queue_url, ReceiptHandle="test-receipt-handle"
        )

    @patch('boto3.client')
    def test_consume_batch_no_messages(self, mock_boto_client):
        """Test consume batch when no messages available."""
        # Arrange
        mock_sqs = Mock()
        mock_boto_client.return_value = mock_sqs
        mock_sqs.receive_message.return_value = {}

        consumer = e2e_telemetry.ConcurrentConsumer(queue_url=self.queue_url)

        # Act
        result = consumer.consume_batch()

        # Assert
        expected = {
            'messages_received': 0,
            'messages_processed': 0,
            'messages_deleted': 0,
        }
        self.assertEqual(result, expected)


class TestE2ETelemetryOrchestrator(unittest.TestCase):
    """Test E2ETelemetryOrchestrator class for main workflow orchestration."""

    def setUp(self):
        """Set up test fixtures."""
        self.queue_url = 'https://sqs.us-east-1.amazonaws.com/123456789/test-queue'

    @patch('boto3.client')
    def test_orchestrator_initialization(self, mock_boto_client):
        """Test E2ETelemetryOrchestrator proper initialization."""
        # Arrange
        mock_sqs = Mock()
        mock_boto_client.return_value = mock_sqs

        # Act
        orchestrator = e2e_telemetry.E2ETelemetryOrchestrator(
            queue_url=self.queue_url, aws_region='us-east-1'
        )

        # Assert
        self.assertEqual(orchestrator.queue_url, self.queue_url)
        self.assertEqual(orchestrator.aws_region, 'us-east-1')

        # Check component initialization
        self.assertIsInstance(orchestrator.queue_monitor, e2e_telemetry.QueueMonitor)
        self.assertIsInstance(
            orchestrator.event_generator, e2e_telemetry.EventGenerator
        )
        self.assertIsInstance(orchestrator.consumer, e2e_telemetry.ConcurrentConsumer)


class TestCreateParser(unittest.TestCase):
    """Test argument parser creation function."""

    def setUp(self):
        """Set up test fixtures."""
        self.parser = e2e_telemetry.create_parser()

    def test_parser_creation(self):
        """Test that parser is created successfully."""
        # Act & Assert
        self.assertIsInstance(self.parser, argparse.ArgumentParser)

    def test_parser_default_arguments(self):
        """Test parser with default arguments."""
        # Act
        args = self.parser.parse_args([])

        # Assert
        self.assertEqual(args.events, 100)
        self.assertEqual(args.max_time, 60)
        self.assertEqual(args.region, "us-east-1")
        self.assertFalse(args.verbose)

    def test_parser_custom_arguments(self):
        """Test parser with custom arguments."""
        # Act
        args = self.parser.parse_args(
            [
                '--events',
                '200',
                '--max-time',
                '120',
                '--region',
                'eu-west-1',
                '--queue-url',
                'https://test-queue-url',
                '--verbose',
            ]
        )

        # Assert
        self.assertEqual(args.events, 200)
        self.assertEqual(args.max_time, 120)
        self.assertEqual(args.region, "eu-west-1")
        self.assertEqual(args.queue_url, "https://test-queue-url")
        self.assertTrue(args.verbose)

    def test_parser_invalid_arguments(self):
        """Test parser with invalid arguments."""
        # Act & Assert
        with self.assertRaises(SystemExit):
            self.parser.parse_args(['--invalid-arg'])


if __name__ == '__main__':
    # Configure logging for tests
    logging.disable(logging.CRITICAL)

    # Run tests
    unittest.main(verbosity=2)
