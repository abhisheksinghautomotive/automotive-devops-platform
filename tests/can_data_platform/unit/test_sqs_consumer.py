"""Comprehensive unit tests for SQSBatchConsumer module."""

import unittest
from unittest.mock import Mock, patch
from botocore.exceptions import ClientError

from projects.can_data_platform.src.consumers.sqs_consumer import SQSBatchConsumer
from projects.can_data_platform.src.consumers.interfaces import BatchConsumerResult
from projects.can_data_platform.src.processors.interfaces import MessageProcessor, ProcessingResult
from projects.can_data_platform.src.metrics.interfaces import LatencyTrackerInterface


class TestSQSBatchConsumer(unittest.TestCase):
    """Test suite for SQSBatchConsumer class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.queue_url = "https://sqs.us-east-1.amazonaws.com/123456789/test-queue"
        self.mock_processor = Mock(spec=MessageProcessor)
        self.mock_latency_tracker = Mock(spec=LatencyTrackerInterface)

    def test_initialization_success(self):
        """Test successful SQSBatchConsumer initialization."""
        # Act
        consumer = SQSBatchConsumer(
            queue_url=self.queue_url,
            message_processor=self.mock_processor,
            latency_tracker=self.mock_latency_tracker,
            region_name="us-west-2",
            batch_size=5,
            max_wait_time=10,
            max_retries=2
        )

        # Assert
        self.assertEqual(consumer.queue_url, self.queue_url)
        self.assertEqual(consumer.message_processor, self.mock_processor)
        self.assertEqual(consumer.latency_tracker, self.mock_latency_tracker)
        self.assertEqual(consumer.batch_size, 5)
        self.assertEqual(consumer.max_wait_time, 10)
        self.assertEqual(consumer.max_retries, 2)

    def test_initialization_defaults(self):
        """Test SQSBatchConsumer initialization with default values."""
        # Act
        consumer = SQSBatchConsumer(
            queue_url=self.queue_url,
            message_processor=self.mock_processor,
            latency_tracker=self.mock_latency_tracker
        )

        # Assert
        self.assertEqual(consumer.batch_size, 10)
        self.assertEqual(consumer.max_wait_time, 20)
        self.assertEqual(consumer.max_retries, 3)

    def test_initialization_empty_queue_url(self):
        """Test SQSBatchConsumer initialization with empty queue URL."""
        # Act & Assert
        with self.assertRaises(ValueError) as context:
            SQSBatchConsumer(
                queue_url="",
                message_processor=self.mock_processor,
                latency_tracker=self.mock_latency_tracker
            )
        
        self.assertEqual(str(context.exception), "Queue URL is required")

    def test_initialization_none_queue_url(self):
        """Test SQSBatchConsumer initialization with None queue URL."""
        # Act & Assert
        with self.assertRaises(ValueError) as context:
            SQSBatchConsumer(
                queue_url=None,
                message_processor=self.mock_processor,
                latency_tracker=self.mock_latency_tracker
            )
        
        self.assertEqual(str(context.exception), "Queue URL is required")

    def test_initialization_batch_size_limits(self):
        """Test batch size is correctly limited to AWS SQS constraints."""
        # Test minimum batch size
        consumer_min = SQSBatchConsumer(
            queue_url=self.queue_url,
            message_processor=self.mock_processor,
            latency_tracker=self.mock_latency_tracker,
            batch_size=0
        )
        self.assertEqual(consumer_min.batch_size, 1)
        
        # Test maximum batch size
        consumer_max = SQSBatchConsumer(
            queue_url=self.queue_url,
            message_processor=self.mock_processor,
            latency_tracker=self.mock_latency_tracker,
            batch_size=15
        )
        self.assertEqual(consumer_max.batch_size, 10)

    @patch('boto3.client')
    def test_sqs_client_initialization(self, mock_boto_client):
        """Test SQS client property initialization."""
        # Arrange
        mock_sqs = Mock()
        mock_boto_client.return_value = mock_sqs
        
        # Act
        consumer = SQSBatchConsumer(
            queue_url=self.queue_url,
            message_processor=self.mock_processor,
            latency_tracker=self.mock_latency_tracker,
            region_name="us-west-2"
        )

        # Assert
        self.assertEqual(consumer.sqs_client, mock_sqs)
        mock_boto_client.assert_called_once_with("sqs", region_name="us-west-2")

    @patch('boto3.client')
    def test_receive_messages_success(self, mock_boto_client):
        """Test successful message receiving."""
        # Arrange
        mock_sqs = Mock()
        mock_boto_client.return_value = mock_sqs
        
        mock_response = {
            'Messages': [
                {
                    'MessageId': 'msg1',
                    'Body': '{"test": "data1"}',
                    'ReceiptHandle': 'handle1'
                },
                {
                    'MessageId': 'msg2',
                    'Body': '{"test": "data2"}',
                    'ReceiptHandle': 'handle2'
                }
            ]
        }
        
        mock_sqs.receive_message.return_value = mock_response
        
        consumer = SQSBatchConsumer(
            queue_url=self.queue_url,
            message_processor=self.mock_processor,
            latency_tracker=self.mock_latency_tracker
        )

        # Act
        result = consumer._receive_messages()

        # Assert
        self.assertEqual(result, mock_response)
        mock_sqs.receive_message.assert_called_once_with(
            QueueUrl=self.queue_url,
            MaxNumberOfMessages=10,
            WaitTimeSeconds=20,
            AttributeNames=['SentTimestamp']
        )

    @patch('boto3.client')
    def test_receive_messages_no_messages(self, mock_boto_client):
        """Test receiving when no messages are available."""
        # Arrange
        mock_sqs = Mock()
        mock_boto_client.return_value = mock_sqs
        mock_sqs.receive_message.return_value = {}
        
        consumer = SQSBatchConsumer(
            queue_url=self.queue_url,
            message_processor=self.mock_processor,
            latency_tracker=self.mock_latency_tracker
        )

        # Act
        result = consumer._receive_messages()

        # Assert
        self.assertEqual(result, {})

    @patch('boto3.client')
    def test_receive_messages_client_error(self, mock_boto_client):
        """Test receiving messages with client error."""
        # Arrange
        mock_sqs = Mock()
        mock_boto_client.return_value = mock_sqs
        mock_sqs.receive_message.side_effect = ClientError(
            error_response={'Error': {'Code': 'AccessDenied'}},
            operation_name='ReceiveMessage'
        )
        
        consumer = SQSBatchConsumer(
            queue_url=self.queue_url,
            message_processor=self.mock_processor,
            latency_tracker=self.mock_latency_tracker
        )

        # Act
        result = consumer._receive_messages()

        # Assert
        self.assertIsNone(result)

    @patch('boto3.client')
    def test_process_messages_success(self, mock_boto_client):
        """Test successful message processing."""
        # Arrange
        mock_boto_client.return_value = Mock()
        
        messages = [
            {'MessageId': 'msg1', 'Body': '{"test": "data1"}', 'ReceiptHandle': 'handle1'},
            {'MessageId': 'msg2', 'Body': '{"test": "data2"}', 'ReceiptHandle': 'handle2'}
        ]
        
        # Mock processor to return success for all messages
        success_result1 = ProcessingResult.success_result(event_timestamp=1234567890.0)
        success_result2 = ProcessingResult.success_result(event_timestamp=1234567891.0)
        self.mock_processor.process_message.side_effect = [success_result1, success_result2]
        
        consumer = SQSBatchConsumer(
            queue_url=self.queue_url,
            message_processor=self.mock_processor,
            latency_tracker=self.mock_latency_tracker
        )

        # Act
        results = consumer._process_messages(messages)

        # Assert
        self.assertEqual(len(results), 2)
        self.assertTrue(all(r.success for r in results))
        self.assertEqual(self.mock_processor.process_message.call_count, 2)
        self.assertEqual(self.mock_latency_tracker.record_e2e_latency.call_count, 2)
        self.assertEqual(self.mock_latency_tracker.step_event.call_count, 2)

    @patch('boto3.client')
    def test_process_messages_with_failures(self, mock_boto_client):
        """Test message processing with some failures."""
        # Arrange
        mock_boto_client.return_value = Mock()
        
        messages = [
            {'MessageId': 'msg1', 'Body': '{"test": "data1"}', 'ReceiptHandle': 'handle1'},
            {'MessageId': 'msg2', 'Body': 'invalid-json', 'ReceiptHandle': 'handle2'}
        ]
        
        # Mock processor to return success for first, failure for second
        success_result = ProcessingResult.success_result()
        failure_result = ProcessingResult.failure_result("Invalid JSON")
        self.mock_processor.process_message.side_effect = [success_result, failure_result]
        
        consumer = SQSBatchConsumer(
            queue_url=self.queue_url,
            message_processor=self.mock_processor,
            latency_tracker=self.mock_latency_tracker
        )

        # Act
        results = consumer._process_messages(messages)

        # Assert
        self.assertEqual(len(results), 2)
        self.assertTrue(results[0].success)
        self.assertFalse(results[1].success)
        self.assertEqual(results[1].error_message, "Invalid JSON")

    @patch('boto3.client')
    def test_process_messages_processor_exception(self, mock_boto_client):
        """Test message processing with processor exception."""
        # Arrange
        mock_boto_client.return_value = Mock()
        
        messages = [
            {'MessageId': 'msg1', 'Body': '{"test": "data1"}', 'ReceiptHandle': 'handle1'}
        ]
        
        # Mock processor to raise exception
        self.mock_processor.process_message.side_effect = ValueError("Processing error")
        
        consumer = SQSBatchConsumer(
            queue_url=self.queue_url,
            message_processor=self.mock_processor,
            latency_tracker=self.mock_latency_tracker
        )

        # Act
        results = consumer._process_messages(messages)

        # Assert
        self.assertEqual(len(results), 1)
        self.assertFalse(results[0].success)
        self.assertEqual(results[0].error_message, "Processing error")

    @patch('boto3.client')
    def test_delete_successful_messages_all_success(self, mock_boto_client):
        """Test deleting messages when all processing succeeded."""
        # Arrange
        mock_sqs = Mock()
        mock_boto_client.return_value = mock_sqs
        
        messages = [
            {'MessageId': 'msg1', 'ReceiptHandle': 'handle1'},
            {'MessageId': 'msg2', 'ReceiptHandle': 'handle2'}
        ]
        
        processing_results = [
            ProcessingResult.success_result(),
            ProcessingResult.success_result()
        ]
        
        mock_sqs.delete_message_batch.return_value = {
            'Successful': [{'Id': 'msg1'}, {'Id': 'msg2'}],
            'Failed': []
        }
        
        consumer = SQSBatchConsumer(
            queue_url=self.queue_url,
            message_processor=self.mock_processor,
            latency_tracker=self.mock_latency_tracker
        )

        # Act
        result = consumer._delete_successful_messages(messages, processing_results)

        # Assert
        self.assertEqual(result['deleted'], 2)
        self.assertEqual(result['errors'], 0)

    @patch('boto3.client')
    def test_delete_successful_messages_mixed_results(self, mock_boto_client):
        """Test deleting messages with mixed processing results."""
        # Arrange
        mock_sqs = Mock()
        mock_boto_client.return_value = mock_sqs
        
        messages = [
            {'MessageId': 'msg1', 'ReceiptHandle': 'handle1'},
            {'MessageId': 'msg2', 'ReceiptHandle': 'handle2'}
        ]
        
        processing_results = [
            ProcessingResult.success_result(),
            ProcessingResult.failure_result("Failed")
        ]
        
        mock_sqs.delete_message_batch.return_value = {
            'Successful': [{'Id': 'msg1'}],
            'Failed': []
        }
        
        consumer = SQSBatchConsumer(
            queue_url=self.queue_url,
            message_processor=self.mock_processor,
            latency_tracker=self.mock_latency_tracker
        )

        # Act
        result = consumer._delete_successful_messages(messages, processing_results)

        # Assert
        self.assertEqual(result['deleted'], 1)
        self.assertEqual(result['errors'], 0)
        # Only successful message should be in deletion request
        expected_entries = [{'Id': 'msg1', 'ReceiptHandle': 'handle1'}]
        mock_sqs.delete_message_batch.assert_called_once_with(
            QueueUrl=self.queue_url,
            Entries=expected_entries
        )

    @patch('boto3.client')
    def test_delete_successful_messages_no_successful(self, mock_boto_client):
        """Test deleting messages when no processing succeeded."""
        # Arrange
        mock_boto_client.return_value = Mock()
        
        messages = [
            {'MessageId': 'msg1', 'ReceiptHandle': 'handle1'}
        ]
        
        processing_results = [
            ProcessingResult.failure_result("Failed")
        ]
        
        consumer = SQSBatchConsumer(
            queue_url=self.queue_url,
            message_processor=self.mock_processor,
            latency_tracker=self.mock_latency_tracker
        )

        # Act
        result = consumer._delete_successful_messages(messages, processing_results)

        # Assert
        self.assertEqual(result['deleted'], 0)
        self.assertEqual(result['errors'], 0)

    @patch('boto3.client')
    def test_delete_messages_with_retry_success(self, mock_boto_client):
        """Test successful message deletion with retry logic."""
        # Arrange
        mock_sqs = Mock()
        mock_boto_client.return_value = mock_sqs
        
        deletion_entries = [
            {'Id': 'msg1', 'ReceiptHandle': 'handle1'}
        ]
        
        mock_sqs.delete_message_batch.return_value = {
            'Successful': [{'Id': 'msg1'}],
            'Failed': []
        }
        
        consumer = SQSBatchConsumer(
            queue_url=self.queue_url,
            message_processor=self.mock_processor,
            latency_tracker=self.mock_latency_tracker
        )

        # Act
        result = consumer._delete_messages_with_retry(deletion_entries)

        # Assert
        self.assertEqual(result['deleted'], 1)
        self.assertEqual(result['errors'], 0)

    @patch('boto3.client')
    @patch('time.sleep')
    def test_delete_messages_with_retry_failures(self, mock_sleep, mock_boto_client):
        """Test message deletion with retries on failure."""
        # Arrange
        mock_sqs = Mock()
        mock_boto_client.return_value = mock_sqs
        
        deletion_entries = [
            {'Id': 'msg1', 'ReceiptHandle': 'handle1'}
        ]
        
        # First call fails, second succeeds
        mock_sqs.delete_message_batch.side_effect = [
            ClientError(
                error_response={'Error': {'Code': 'ServiceUnavailable'}},
                operation_name='DeleteMessageBatch'
            ),
            {
                'Successful': [{'Id': 'msg1'}],
                'Failed': []
            }
        ]
        
        consumer = SQSBatchConsumer(
            queue_url=self.queue_url,
            message_processor=self.mock_processor,
            latency_tracker=self.mock_latency_tracker,
            max_retries=2
        )

        # Act
        result = consumer._delete_messages_with_retry(deletion_entries)

        # Assert
        self.assertEqual(result['deleted'], 1)
        self.assertEqual(result['errors'], 0)
        mock_sleep.assert_called_once_with(2)

    @patch('boto3.client')
    def test_consume_batch_full_workflow(self, mock_boto_client):
        """Test complete consume_batch workflow."""
        # Arrange
        mock_sqs = Mock()
        mock_boto_client.return_value = mock_sqs
        
        # Mock messages
        mock_messages = [
            {'MessageId': 'msg1', 'Body': '{"test": "data1"}', 'ReceiptHandle': 'handle1'},
            {'MessageId': 'msg2', 'Body': '{"test": "data2"}', 'ReceiptHandle': 'handle2'}
        ]
        
        mock_sqs.receive_message.return_value = {'Messages': mock_messages}
        mock_sqs.delete_message_batch.return_value = {
            'Successful': [{'Id': 'msg1'}, {'Id': 'msg2'}],
            'Failed': []
        }
        
        # Mock successful processing
        success_result1 = ProcessingResult.success_result()
        success_result2 = ProcessingResult.success_result()
        self.mock_processor.process_message.side_effect = [success_result1, success_result2]
        
        # Mock latency tracker methods
        self.mock_latency_tracker.should_flush.return_value = False
        
        consumer = SQSBatchConsumer(
            queue_url=self.queue_url,
            message_processor=self.mock_processor,
            latency_tracker=self.mock_latency_tracker
        )

        # Act
        result = consumer.consume_batch()

        # Assert
        self.assertIsInstance(result, BatchConsumerResult)
        self.assertEqual(result.consumed, 2)
        self.assertEqual(result.messages_processed, 2)
        self.assertEqual(result.messages_deleted, 2)
        self.assertEqual(result.errors, 0)
        self.assertEqual(result.deletion_errors, 0)
        self.assertGreater(result.processing_time, 0)

    @patch('boto3.client')
    def test_consume_batch_no_messages(self, mock_boto_client):
        """Test consume_batch with no messages available."""
        # Arrange
        mock_sqs = Mock()
        mock_boto_client.return_value = mock_sqs
        mock_sqs.receive_message.return_value = {}
        
        consumer = SQSBatchConsumer(
            queue_url=self.queue_url,
            message_processor=self.mock_processor,
            latency_tracker=self.mock_latency_tracker
        )

        # Act
        result = consumer.consume_batch()

        # Assert
        self.assertEqual(result.consumed, 0)
        self.assertEqual(result.messages_processed, 0)
        self.assertEqual(result.messages_deleted, 0)

    @patch('boto3.client')
    def test_consume_batch_receive_failure(self, mock_boto_client):
        """Test consume_batch when receiving messages fails."""
        # Arrange
        mock_sqs = Mock()
        mock_boto_client.return_value = mock_sqs
        mock_sqs.receive_message.side_effect = ClientError(
            error_response={'Error': {'Code': 'AccessDenied'}},
            operation_name='ReceiveMessage'
        )
        
        consumer = SQSBatchConsumer(
            queue_url=self.queue_url,
            message_processor=self.mock_processor,
            latency_tracker=self.mock_latency_tracker
        )

        # Act
        result = consumer.consume_batch()

        # Assert
        self.assertEqual(result.consumed, 0)
        self.assertEqual(consumer.consecutive_failures, 1)

    def test_is_healthy_when_healthy(self):
        """Test is_healthy returns True when consumer is healthy."""
        # Arrange
        consumer = SQSBatchConsumer(
            queue_url=self.queue_url,
            message_processor=self.mock_processor,
            latency_tracker=self.mock_latency_tracker
        )
        consumer.consecutive_failures = 3

        # Act & Assert
        self.assertTrue(consumer.is_healthy())

    def test_is_healthy_when_unhealthy(self):
        """Test is_healthy returns False when consumer is unhealthy."""
        # Arrange
        consumer = SQSBatchConsumer(
            queue_url=self.queue_url,
            message_processor=self.mock_processor,
            latency_tracker=self.mock_latency_tracker
        )
        consumer.consecutive_failures = 5

        # Act & Assert
        self.assertFalse(consumer.is_healthy())

    def test_health_check_alias(self):
        """Test health_check method is an alias for is_healthy."""
        # Arrange
        consumer = SQSBatchConsumer(
            queue_url=self.queue_url,
            message_processor=self.mock_processor,
            latency_tracker=self.mock_latency_tracker
        )

        # Act & Assert
        self.assertEqual(consumer.health_check(), consumer.is_healthy())

    def test_close_method(self):
        """Test close method executes without error."""
        # Arrange
        consumer = SQSBatchConsumer(
            queue_url=self.queue_url,
            message_processor=self.mock_processor,
            latency_tracker=self.mock_latency_tracker
        )

        # Act & Assert - should not raise exception
        consumer.close()


if __name__ == '__main__':
    unittest.main(verbosity=2)