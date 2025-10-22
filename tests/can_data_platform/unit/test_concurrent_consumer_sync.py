"""Synchronous tests for ConcurrentSQSConsumer to avoid async hangs."""

import json
import time
import unittest
from unittest.mock import Mock, patch

from botocore.exceptions import BotoCoreError, ClientError

from projects.can_data_platform.src.consumers.concurrent_sqs_consumer import (
    ConcurrentSQSConsumer,
)


class TestConcurrentSQSConsumerSync(unittest.TestCase):
    """Synchronous test cases for ConcurrentSQSConsumer."""

    def setUp(self):
        """Set up test fixtures."""
        self.queue_url = "https://sqs.us-east-1.amazonaws.com/123/test"
        self.mock_processor = Mock()
        self.mock_latency_tracker = Mock()

    @patch('boto3.client')
    def test_initialization_success(self, mock_boto):
        """Test successful initialization."""
        consumer = ConcurrentSQSConsumer(
            queue_url=self.queue_url,
            processor=self.mock_processor,
            latency_tracker=self.mock_latency_tracker,
            max_workers=2,
            poll_interval=0.1,
            batch_size=5,
            sla_threshold_seconds=3.0,
        )

        self.assertEqual(consumer.queue_url, self.queue_url)
        self.assertEqual(consumer.processor, self.mock_processor)
        self.assertEqual(consumer.max_workers, 2)
        self.assertEqual(consumer.poll_interval, 0.1)
        self.assertEqual(consumer.batch_size, 5)
        self.assertEqual(consumer.sla_threshold_seconds, 3.0)
        self.assertFalse(consumer.running)
        self.assertEqual(consumer.processed_count, 0)
        self.assertEqual(consumer.error_count, 0)

    @patch('boto3.client')
    def test_fetch_messages_success(self, mock_boto):
        """Test successful message fetching."""
        mock_sqs = Mock()
        mock_boto.return_value = mock_sqs

        messages = [
            {'MessageId': '1', 'Body': '{"data": "test1"}', 'ReceiptHandle': 'rh1'},
            {'MessageId': '2', 'Body': '{"data": "test2"}', 'ReceiptHandle': 'rh2'},
        ]

        mock_sqs.receive_message.return_value = {'Messages': messages}

        consumer = ConcurrentSQSConsumer(
            queue_url=self.queue_url,
            processor=self.mock_processor,
            latency_tracker=self.mock_latency_tracker,
        )

        result = consumer._fetch_messages()

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['MessageId'], '1')
        mock_sqs.receive_message.assert_called_once_with(
            QueueUrl=self.queue_url,
            MaxNumberOfMessages=10,
            WaitTimeSeconds=0,
            MessageAttributeNames=['All'],
        )

    @patch('boto3.client')
    def test_fetch_messages_empty_response(self, mock_boto):
        """Test fetching with no messages available."""
        mock_sqs = Mock()
        mock_boto.return_value = mock_sqs
        mock_sqs.receive_message.return_value = {}

        consumer = ConcurrentSQSConsumer(
            queue_url=self.queue_url,
            processor=self.mock_processor,
            latency_tracker=self.mock_latency_tracker,
        )

        result = consumer._fetch_messages()

        self.assertEqual(len(result), 0)

    @patch('boto3.client')
    def test_fetch_messages_boto_error(self, mock_boto):
        """Test fetching with BotoCoreError."""
        mock_sqs = Mock()
        mock_boto.return_value = mock_sqs
        mock_sqs.receive_message.side_effect = BotoCoreError()

        consumer = ConcurrentSQSConsumer(
            queue_url=self.queue_url,
            processor=self.mock_processor,
            latency_tracker=self.mock_latency_tracker,
        )

        result = consumer._fetch_messages()

        self.assertEqual(len(result), 0)

    @patch('boto3.client')
    def test_fetch_messages_client_error(self, mock_boto):
        """Test fetching with ClientError."""
        mock_sqs = Mock()
        mock_boto.return_value = mock_sqs
        error_response = {'Error': {'Code': 'AccessDenied', 'Message': 'Denied'}}
        mock_sqs.receive_message.side_effect = ClientError(error_response, 'ReceiveMessage')

        consumer = ConcurrentSQSConsumer(
            queue_url=self.queue_url,
            processor=self.mock_processor,
            latency_tracker=self.mock_latency_tracker,
        )

        result = consumer._fetch_messages()

        self.assertEqual(len(result), 0)

    @patch('boto3.client')
    def test_delete_messages_success(self, mock_boto):
        """Test successful message deletion."""
        mock_sqs = Mock()
        mock_boto.return_value = mock_sqs

        consumer = ConcurrentSQSConsumer(
            queue_url=self.queue_url,
            processor=self.mock_processor,
            latency_tracker=self.mock_latency_tracker,
        )

        receipts = ['rh1', 'rh2', 'rh3']
        consumer._delete_messages(receipts)

        mock_sqs.delete_message_batch.assert_called_once()
        call_args = mock_sqs.delete_message_batch.call_args
        self.assertEqual(call_args[1]['QueueUrl'], self.queue_url)
        self.assertEqual(len(call_args[1]['Entries']), 3)

    @patch('boto3.client')
    def test_delete_messages_large_batch(self, mock_boto):
        """Test deleting more than 10 messages (batch limit)."""
        mock_sqs = Mock()
        mock_boto.return_value = mock_sqs

        consumer = ConcurrentSQSConsumer(
            queue_url=self.queue_url,
            processor=self.mock_processor,
            latency_tracker=self.mock_latency_tracker,
        )

        # 15 messages - should be split into 2 batches
        receipts = [f'rh{i}' for i in range(15)]
        consumer._delete_messages(receipts)

        self.assertEqual(mock_sqs.delete_message_batch.call_count, 2)

    @patch('boto3.client')
    def test_delete_messages_boto_error(self, mock_boto):
        """Test deletion with BotoCoreError."""
        mock_sqs = Mock()
        mock_boto.return_value = mock_sqs
        mock_sqs.delete_message_batch.side_effect = BotoCoreError()

        consumer = ConcurrentSQSConsumer(
            queue_url=self.queue_url,
            processor=self.mock_processor,
            latency_tracker=self.mock_latency_tracker,
        )

        # Should handle error gracefully
        receipts = ['rh1', 'rh2']
        consumer._delete_messages(receipts)

    @patch('boto3.client')
    def test_delete_messages_client_error(self, mock_boto):
        """Test deletion with ClientError."""
        mock_sqs = Mock()
        mock_boto.return_value = mock_sqs
        error_response = {'Error': {'Code': 'InvalidRequest', 'Message': 'Invalid'}}
        mock_sqs.delete_message_batch.side_effect = ClientError(error_response, 'DeleteMessageBatch')

        consumer = ConcurrentSQSConsumer(
            queue_url=self.queue_url,
            processor=self.mock_processor,
            latency_tracker=self.mock_latency_tracker,
        )

        receipts = ['rh1']
        consumer._delete_messages(receipts)

    @patch('boto3.client')
    def test_stop_method(self, mock_boto):
        """Test stop method sets running flag to False."""
        consumer = ConcurrentSQSConsumer(
            queue_url=self.queue_url,
            processor=self.mock_processor,
            latency_tracker=self.mock_latency_tracker,
        )

        consumer.running = True
        consumer.stop()

        self.assertFalse(consumer.running)


class TestConcurrentSQSConsumerProcessing(unittest.TestCase):
    """Test message processing logic."""

    def setUp(self):
        """Set up test fixtures."""
        self.queue_url = "https://sqs.us-east-1.amazonaws.com/123/test"
        self.mock_processor = Mock()
        self.mock_latency_tracker = Mock()

    @patch('boto3.client')
    def test_process_single_message_success(self, mock_boto):
        """Test successful single message processing."""
        mock_boto.return_value = Mock()

        self.mock_processor.process_message.return_value = None

        consumer = ConcurrentSQSConsumer(
            queue_url=self.queue_url,
            processor=self.mock_processor,
            latency_tracker=self.mock_latency_tracker,
            sla_threshold_seconds=5.0,
        )

        message = {
            'MessageId': '1',
            'Body': json.dumps({'timestamp': time.time() - 1.0, 'data': 'test'}),
            'ReceiptHandle': 'rh1',
        }

        # Use asyncio.run to test async method
        import asyncio
        result = asyncio.run(consumer._process_single_message(message))

        self.assertTrue(result)
        self.mock_processor.process_message.assert_called_once()
        self.mock_latency_tracker.record_e2e_latency.assert_called_once()
        self.mock_latency_tracker.step_event.assert_called_once()

    @patch('boto3.client')
    def test_process_single_message_sla_violation(self, mock_boto):
        """Test message processing with SLA violation."""
        mock_boto.return_value = Mock()

        self.mock_processor.process_message.return_value = None

        consumer = ConcurrentSQSConsumer(
            queue_url=self.queue_url,
            processor=self.mock_processor,
            latency_tracker=self.mock_latency_tracker,
            sla_threshold_seconds=2.0,
        )

        # Message older than SLA threshold
        message = {
            'MessageId': '1',
            'Body': json.dumps({'timestamp': time.time() - 5.0, 'data': 'test'}),
            'ReceiptHandle': 'rh1',
        }

        import asyncio
        result = asyncio.run(consumer._process_single_message(message))

        self.assertTrue(result)
        # Should still process successfully

    @patch('boto3.client')
    def test_process_single_message_json_decode_error(self, mock_boto):
        """Test message processing with invalid JSON."""
        mock_boto.return_value = Mock()

        consumer = ConcurrentSQSConsumer(
            queue_url=self.queue_url,
            processor=self.mock_processor,
            latency_tracker=self.mock_latency_tracker,
        )

        message = {
            'MessageId': '1',
            'Body': 'invalid json{',
            'ReceiptHandle': 'rh1',
        }

        import asyncio
        result = asyncio.run(consumer._process_single_message(message))

        self.assertFalse(result)

    @patch('boto3.client')
    def test_process_single_message_key_error(self, mock_boto):
        """Test message processing with missing timestamp key."""
        mock_boto.return_value = Mock()

        self.mock_processor.process_message.return_value = None

        consumer = ConcurrentSQSConsumer(
            queue_url=self.queue_url,
            processor=self.mock_processor,
            latency_tracker=self.mock_latency_tracker,
        )

        # Message without timestamp (but JSON is valid)
        message = {
            'MessageId': '1',
            'Body': json.dumps({'data': 'test'}),
            'ReceiptHandle': 'rh1',
        }

        import asyncio
        result = asyncio.run(consumer._process_single_message(message))

        # Should succeed - timestamp has a default
        self.assertTrue(result)

    @patch('boto3.client')
    def test_process_messages_concurrent_success(self, mock_boto):
        """Test concurrent processing of multiple messages."""
        mock_boto.return_value = Mock()

        self.mock_processor.process_message.return_value = None

        consumer = ConcurrentSQSConsumer(
            queue_url=self.queue_url,
            processor=self.mock_processor,
            latency_tracker=self.mock_latency_tracker,
        )

        messages = [
            {
                'MessageId': f'{i}',
                'Body': json.dumps({'timestamp': time.time(), 'data': f'test{i}'}),
                'ReceiptHandle': f'rh{i}',
            }
            for i in range(3)
        ]

        import asyncio
        asyncio.run(consumer._process_messages_concurrent(messages))

        # Should process all messages
        self.assertEqual(self.mock_processor.process_message.call_count, 3)
        self.assertEqual(consumer.processed_count, 3)
        self.assertEqual(consumer.error_count, 0)

    @patch('boto3.client')
    def test_process_messages_concurrent_with_errors(self, mock_boto):
        """Test concurrent processing with some message failures."""
        mock_sqs = Mock()
        mock_boto.return_value = mock_sqs

        # First call succeeds, second fails
        self.mock_processor.process_message.side_effect = [None, ValueError("Bad message"), None]

        consumer = ConcurrentSQSConsumer(
            queue_url=self.queue_url,
            processor=self.mock_processor,
            latency_tracker=self.mock_latency_tracker,
        )

        messages = [
            {
                'MessageId': f'{i}',
                'Body': json.dumps({'timestamp': time.time(), 'data': f'test{i}'}),
                'ReceiptHandle': f'rh{i}',
            }
            for i in range(3)
        ]

        import asyncio
        asyncio.run(consumer._process_messages_concurrent(messages))

        # Should have 2 successes, 1 error
        self.assertEqual(consumer.processed_count, 2)
        self.assertEqual(consumer.error_count, 1)

    @patch('boto3.client')
    def test_executor_shutdown(self, mock_boto):
        """Test executor shutdown on consumer stop."""
        consumer = ConcurrentSQSConsumer(
            queue_url=self.queue_url,
            processor=self.mock_processor,
            latency_tracker=self.mock_latency_tracker,
        )

        with patch.object(consumer.executor, 'shutdown'):
            consumer.stop()
            # Executor should not be shut down by stop method alone
            # It's handled in start_consuming's finally block


if __name__ == "__main__":
    unittest.main()
