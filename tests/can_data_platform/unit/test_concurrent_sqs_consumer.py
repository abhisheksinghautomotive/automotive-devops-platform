"""Unit tests for ConcurrentSQSConsumer using comprehensive testing patterns."""

import asyncio
import unittest
import json
from unittest.mock import Mock, patch

from botocore.exceptions import BotoCoreError, ClientError

from projects.can_data_platform.src.consumers.concurrent_sqs_consumer import ConcurrentSQSConsumer
from projects.can_data_platform.src.metrics.interfaces import LatencyTrackerInterface


class TestConcurrentSQSConsumer(unittest.TestCase):
    """Test cases for ConcurrentSQSConsumer class."""

    def setUp(self):
        """Set up test fixtures for each test method."""
        self.queue_url = "https://sqs.us-east-1.amazonaws.com/123456789012/test-queue"
        self.mock_processor = Mock()
        self.mock_latency_tracker = Mock(spec=LatencyTrackerInterface)
        
        # Default configuration
        self.max_workers = 2
        self.poll_interval = 0.1
        self.batch_size = 5
        self.sla_threshold = 5.0

        # Create consumer instance
        with patch('boto3.client'):
            self.consumer = ConcurrentSQSConsumer(
                queue_url=self.queue_url,
                processor=self.mock_processor,
                latency_tracker=self.mock_latency_tracker,
                max_workers=self.max_workers,
                poll_interval=self.poll_interval,
                batch_size=self.batch_size,
                sla_threshold_seconds=self.sla_threshold,
            )

    def test_initialization_success(self):
        """Test successful ConcurrentSQSConsumer initialization."""
        with patch('boto3.client') as mock_boto:
            consumer = ConcurrentSQSConsumer(
                queue_url=self.queue_url,
                processor=self.mock_processor,
                latency_tracker=self.mock_latency_tracker,
                max_workers=4,
                poll_interval=0.2,
                batch_size=10,
                sla_threshold_seconds=3.0,
            )

            # Assert all parameters are set correctly
            self.assertEqual(consumer.queue_url, self.queue_url)
            self.assertEqual(consumer.processor, self.mock_processor)
            self.assertEqual(consumer.latency_tracker, self.mock_latency_tracker)
            self.assertEqual(consumer.max_workers, 4)
            self.assertEqual(consumer.poll_interval, 0.2)
            self.assertEqual(consumer.batch_size, 10)
            self.assertEqual(consumer.sla_threshold_seconds, 3.0)
            self.assertFalse(consumer.running)
            self.assertEqual(consumer.processed_count, 0)
            self.assertEqual(consumer.error_count, 0)
            
            # Assert boto3 client is created
            mock_boto.assert_called_once_with('sqs')

    def test_initialization_defaults(self):
        """Test initialization with default parameters."""
        with patch('boto3.client'):
            consumer = ConcurrentSQSConsumer(
                queue_url=self.queue_url,
                processor=self.mock_processor,
                latency_tracker=self.mock_latency_tracker,
            )

            self.assertEqual(consumer.max_workers, 4)
            self.assertEqual(consumer.poll_interval, 0.1)
            self.assertEqual(consumer.batch_size, 10)
            self.assertEqual(consumer.max_retries, 3)
            self.assertEqual(consumer.sla_threshold_seconds, 5.0)

    def test_fetch_messages_success(self):
        """Test successful message fetching from SQS."""
        # Arrange
        mock_messages = [
            {"MessageId": "1", "Body": '{"test": "data1"}', "ReceiptHandle": "receipt1"},
            {"MessageId": "2", "Body": '{"test": "data2"}', "ReceiptHandle": "receipt2"},
        ]
        self.consumer.sqs.receive_message.return_value = {"Messages": mock_messages}

        # Act
        result = self.consumer._fetch_messages()

        # Assert
        self.assertEqual(result, mock_messages)
        self.consumer.sqs.receive_message.assert_called_once_with(
            QueueUrl=self.queue_url,
            MaxNumberOfMessages=self.batch_size,
            WaitTimeSeconds=0,
            MessageAttributeNames=['All'],
        )

    def test_fetch_messages_no_messages(self):
        """Test fetching when no messages are available."""
        # Arrange
        self.consumer.sqs.receive_message.return_value = {}

        # Act
        result = self.consumer._fetch_messages()

        # Assert
        self.assertEqual(result, [])

    def test_fetch_messages_boto_error(self):
        """Test fetching messages with BotoCore error."""
        # Arrange
        self.consumer.sqs.receive_message.side_effect = BotoCoreError()

        # Act
        result = self.consumer._fetch_messages()

        # Assert
        self.assertEqual(result, [])

    def test_fetch_messages_client_error(self):
        """Test fetching messages with Client error."""
        # Arrange
        self.consumer.sqs.receive_message.side_effect = ClientError(
            error_response={'Error': {'Code': 'AccessDenied'}},
            operation_name='ReceiveMessage'
        )

        # Act
        result = self.consumer._fetch_messages()

        # Assert
        self.assertEqual(result, [])

    @patch('time.time')
    def test_process_single_message_success(self, mock_time):
        """Test successful single message processing."""
        # Mock time
        mock_time.side_effect = [1000.0, 1001.0]  # start, end
        
        # Arrange
        message = {
            "Body": json.dumps({"timestamp": "2024-01-01T00:00:00", "signal": "test"}),
            "ReceiptHandle": "receipt123"
        }

        # Mock async execution
        with patch('asyncio.get_event_loop') as mock_loop:
            mock_future = asyncio.Future()
            mock_future.set_result(None)
            mock_loop.return_value.run_in_executor.return_value = mock_future
            
            # Test using asyncio.run
            result = asyncio.run(self.consumer._process_single_message(message))

        # Assert
        self.assertTrue(result)
        self.mock_latency_tracker.record_e2e_latency.assert_called_once()

    @patch('time.time')
    async def test_process_single_message_sla_violation(self, mock_time):
        """Test processing message with SLA violation."""
        # Arrange
        mock_time.side_effect = [1010.0]  # process_timestamp - exceeds threshold
        message = {
            "Body": '{"timestamp": 1000.0, "data": "test"}',
            "ReceiptHandle": "receipt1"
        }
        self.mock_processor.process_message.return_value = None

        # Act
        with patch('asyncio.get_event_loop') as mock_loop:
            mock_loop.return_value.run_in_executor.return_value = asyncio.Future()
            mock_loop.return_value.run_in_executor.return_value.set_result(None)
            
            result = await self.consumer._process_single_message(message)

        # Assert
        self.assertTrue(result)
        # SLA violation should be logged (10s > 5s threshold)

    async def test_process_single_message_json_decode_error(self):
        """Test processing message with invalid JSON."""
        # Arrange
        message = {
            "Body": "invalid json",
            "ReceiptHandle": "receipt1"
        }

        # Act
        result = await self.consumer._process_single_message(message)

        # Assert
        self.assertFalse(result)

    @patch('time.time')
    async def test_process_single_message_no_timestamp(self, mock_time):
        """Test processing message without timestamp."""
        # Arrange
        mock_time.side_effect = [1000.0, 1000.0]  # Both event and process timestamp
        message = {
            "Body": '{"data": "test"}',  # No timestamp
            "ReceiptHandle": "receipt1"
        }
        self.mock_processor.process_message.return_value = None

        # Act
        with patch('asyncio.get_event_loop') as mock_loop:
            mock_loop.return_value.run_in_executor.return_value = asyncio.Future()
            mock_loop.return_value.run_in_executor.return_value.set_result(None)
            
            result = await self.consumer._process_single_message(message)

        # Assert
        self.assertTrue(result)
        # Should use process_timestamp as event_timestamp
        self.mock_latency_tracker.record_e2e_latency.assert_called_once_with(1000.0, 1000.0)

    def test_delete_messages_success(self):
        """Test successful deletion of messages."""
        # Arrange
        receipt_handles = ["receipt1", "receipt2", "receipt3"]

        # Act
        self.consumer._delete_messages(receipt_handles)

        # Assert
        self.consumer.sqs.delete_message_batch.assert_called_once_with(
            QueueUrl=self.queue_url,
            Entries=[
                {'Id': '0', 'ReceiptHandle': 'receipt1'},
                {'Id': '1', 'ReceiptHandle': 'receipt2'},
                {'Id': '2', 'ReceiptHandle': 'receipt3'},
            ]
        )

    def test_delete_messages_large_batch(self):
        """Test deletion of messages in large batches (>10)."""
        # Arrange
        receipt_handles = [f"receipt{i}" for i in range(15)]

        # Act
        self.consumer._delete_messages(receipt_handles)

        # Assert
        # Should make 2 calls: first 10, then remaining 5
        self.assertEqual(self.consumer.sqs.delete_message_batch.call_count, 2)

    def test_delete_messages_boto_error(self):
        """Test deletion with BotoCore error."""
        # Arrange
        receipt_handles = ["receipt1"]
        self.consumer.sqs.delete_message_batch.side_effect = BotoCoreError()

        # Act - should not raise exception
        self.consumer._delete_messages(receipt_handles)

        # Assert
        self.consumer.sqs.delete_message_batch.assert_called_once()

    def test_delete_messages_client_error(self):
        """Test deletion with Client error."""
        # Arrange
        receipt_handles = ["receipt1"]
        self.consumer.sqs.delete_message_batch.side_effect = ClientError(
            error_response={'Error': {'Code': 'InvalidReceiptHandle'}},
            operation_name='DeleteMessageBatch'
        )

        # Act - should not raise exception
        self.consumer._delete_messages(receipt_handles)

        # Assert
        self.consumer.sqs.delete_message_batch.assert_called_once()

    @patch('time.time')
    async def test_process_messages_concurrent_success(self, mock_time):
        """Test concurrent processing of messages."""
        # Arrange
        mock_time.side_effect = [2000.0, 2001.0]  # batch start/end
        messages = [
            {"Body": '{"test": "data1"}', "ReceiptHandle": "receipt1"},
            {"Body": '{"test": "data2"}', "ReceiptHandle": "receipt2"},
        ]

        with patch.object(self.consumer, '_process_single_message') as mock_process:
            mock_process.return_value = True
            with patch.object(self.consumer, '_delete_messages') as mock_delete:
                # Act
                await self.consumer._process_messages_concurrent(messages)

                # Assert
                self.assertEqual(mock_process.call_count, 2)
                self.assertEqual(self.consumer.processed_count, 2)
                self.assertEqual(self.consumer.error_count, 0)
                mock_delete.assert_called_once_with(["receipt1", "receipt2"])
                self.mock_latency_tracker.record_batch_write_latency.assert_called_once_with(2000.0, 2001.0)

    @patch('time.time')
    async def test_process_messages_concurrent_with_errors(self, mock_time):
        """Test concurrent processing with some errors."""
        # Arrange
        mock_time.side_effect = [2000.0, 2001.0]
        messages = [
            {"Body": '{"test": "data1"}', "ReceiptHandle": "receipt1"},
            {"Body": '{"test": "data2"}', "ReceiptHandle": "receipt2"},
        ]

        with patch.object(self.consumer, '_process_single_message') as mock_process:
            # First succeeds, second fails
            mock_process.side_effect = [True, Exception("Processing error")]
            with patch.object(self.consumer, '_delete_messages') as mock_delete:
                # Act
                await self.consumer._process_messages_concurrent(messages)

                # Assert
                self.assertEqual(self.consumer.processed_count, 1)
                self.assertEqual(self.consumer.error_count, 1)
                mock_delete.assert_called_once_with(["receipt1"])

    async def test_process_messages_concurrent_no_successful(self):
        """Test concurrent processing with no successful messages."""
        # Arrange
        messages = [
            {"Body": '{"test": "data1"}', "ReceiptHandle": "receipt1"},
        ]

        with patch.object(self.consumer, '_process_single_message') as mock_process:
            mock_process.side_effect = [Exception("Processing error")]
            with patch.object(self.consumer, '_delete_messages') as mock_delete:
                # Act
                await self.consumer._process_messages_concurrent(messages)

                # Assert
                self.assertEqual(self.consumer.processed_count, 0)
                self.assertEqual(self.consumer.error_count, 1)
                mock_delete.assert_not_called()

    @patch('time.time')
    async def test_start_consuming_with_messages(self, mock_time):
        """Test start_consuming with messages available."""
        # Arrange
        mock_time.side_effect = [3000.0, 3001.0]  # poll start/end
        messages = [{"Body": '{"test": "data"}', "ReceiptHandle": "receipt1"}]
        
        # Mock to stop after one iteration
        call_count = 0

        def mock_fetch():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return messages
            else:
                self.consumer.running = False
                return []

        with patch.object(self.consumer, '_fetch_messages', side_effect=mock_fetch):
            with patch.object(self.consumer, '_process_messages_concurrent') as mock_process:
                # Act
                result = await self.consumer.start_consuming()

                # Assert
                self.assertIn("processed", result)
                self.assertIn("errors", result)
                self.assertIn("success_rate", result)
                mock_process.assert_called_once_with(messages)
                self.mock_latency_tracker.record_sqs_latency.assert_called_once_with(3000.0, 3001.0)

    async def test_start_consuming_no_messages(self):
        """Test start_consuming with no messages."""
        # Arrange
        call_count = 0

        def mock_fetch():
            nonlocal call_count
            call_count += 1
            if call_count >= 2:
                self.consumer.running = False
            return []

        with patch.object(self.consumer, '_fetch_messages', side_effect=mock_fetch):
            with patch('asyncio.sleep') as mock_sleep:
                # Act
                result = await self.consumer.start_consuming()

                # Assert
                self.assertEqual(result["processed"], 0)
                self.assertEqual(result["errors"], 0)
                mock_sleep.assert_called_with(self.poll_interval)

    async def test_start_consuming_with_exception(self):
        """Test start_consuming with exception during processing."""
        # Arrange
        with patch.object(self.consumer, '_fetch_messages', side_effect=Exception("Fetch error")):
            # Act & Assert
            with self.assertRaises(Exception):
                await self.consumer.start_consuming()

    def test_stop_consumer(self):
        """Test stopping the consumer."""
        # Arrange
        self.consumer.running = True

        # Act
        self.consumer.stop()

        # Assert
        self.assertFalse(self.consumer.running)

    def test_success_rate_calculation(self):
        """Test success rate calculation in start_consuming."""
        # Arrange
        self.consumer.processed_count = 8
        self.consumer.error_count = 2

        # Act
        async def test():
            self.consumer.running = False
            with patch.object(self.consumer, '_fetch_messages', return_value=[]):
                return await self.consumer.start_consuming()

        result = asyncio.run(test())

        # Assert
        self.assertEqual(result["processed"], 8)
        self.assertEqual(result["errors"], 2)
        self.assertEqual(result["success_rate"], 80.0)  # 8/(8+2) * 100

    def test_success_rate_calculation_no_messages(self):
        """Test success rate calculation with no messages processed."""
        # Arrange
        self.consumer.processed_count = 0
        self.consumer.error_count = 0

        # Act
        async def test():
            self.consumer.running = False
            with patch.object(self.consumer, '_fetch_messages', return_value=[]):
                return await self.consumer.start_consuming()

        result = asyncio.run(test())

        # Assert
        self.assertEqual(result["success_rate"], 0.0)  # 0/max(1,0) * 100

    @patch('projects.can_data_platform.src.consumers.concurrent_sqs_consumer.ThreadPoolExecutor')
    def test_thread_pool_executor_initialization(self, mock_executor):
        """Test ThreadPoolExecutor initialization."""
        # Arrange & Act
        with patch('boto3.client'):
            ConcurrentSQSConsumer(
                queue_url=self.queue_url,
                processor=self.mock_processor,
                latency_tracker=self.mock_latency_tracker,
                max_workers=8,
            )

        # Assert
        mock_executor.assert_called_once_with(max_workers=8)

    def test_executor_shutdown_on_consuming_end(self):
        """Test executor shutdown when consuming ends."""
        # Arrange
        mock_executor = Mock()
        self.consumer.executor = mock_executor

        # Mock to stop immediately and avoid hanging
        async def test():
            self.consumer.running = False
            with patch.object(self.consumer, '_fetch_messages', return_value=[]):
                return await self.consumer.start_consuming()

        # Act
        result = asyncio.run(test())

        # Assert
        mock_executor.shutdown.assert_called_once_with(wait=True)
        self.assertIsInstance(result, dict)


if __name__ == '__main__':
    unittest.main(verbosity=2)
