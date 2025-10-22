"""Comprehensive unit tests for SQS publisher modules."""

import json
import unittest
from unittest.mock import Mock, patch
from botocore.exceptions import ClientError

from projects.can_data_platform.src.publishers.sqs_publisher import SQSPublisher, BatchSQSPublisher
from projects.can_data_platform.src.publishers.interfaces import PublishResult


class TestSQSPublisher(unittest.TestCase):
    """Test suite for SQSPublisher class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.queue_url = "https://sqs.us-east-1.amazonaws.com/123456789/test-queue"
        self.region_name = "us-west-2"

    def test_initialization_success(self):
        """Test successful SQSPublisher initialization."""
        # Act
        publisher = SQSPublisher(
            queue_url=self.queue_url,
            region_name=self.region_name
        )

        # Assert
        self.assertEqual(publisher.queue_url, self.queue_url)
        self.assertEqual(publisher.region_name, self.region_name)

    def test_initialization_empty_queue_url(self):
        """Test SQSPublisher initialization with empty queue URL."""
        # Act & Assert
        with self.assertRaises(ValueError) as context:
            SQSPublisher(queue_url="")
        
        self.assertEqual(str(context.exception), "SQS queue URL is required")

    def test_initialization_none_queue_url(self):
        """Test SQSPublisher initialization with None queue URL."""
        # Act & Assert
        with self.assertRaises(ValueError) as context:
            SQSPublisher(queue_url=None)
        
        self.assertEqual(str(context.exception), "SQS queue URL is required")

    def test_initialization_default_region(self):
        """Test SQSPublisher initialization with default region."""
        # Act
        publisher = SQSPublisher(queue_url=self.queue_url)

        # Assert
        self.assertEqual(publisher.region_name, "us-east-1")

    @patch('boto3.client')
    def test_sqs_client_initialization(self, mock_boto_client):
        """Test SQS client initialization."""
        # Arrange
        mock_sqs = Mock()
        mock_boto_client.return_value = mock_sqs

        # Act
        publisher = SQSPublisher(
            queue_url=self.queue_url,
            region_name=self.region_name
        )

        # Assert
        self.assertEqual(publisher.sqs_client, mock_sqs)
        mock_boto_client.assert_called_once_with("sqs", region_name=self.region_name)

    @patch('boto3.client')
    @patch('time.time')
    def test_publish_single_event_success(self, mock_time, mock_boto_client):
        """Test successful single event publishing."""
        # Arrange
        mock_sqs = Mock()
        mock_boto_client.return_value = mock_sqs
        mock_time.return_value = 1234567890.0

        events = [{"sensor_id": "temp_01", "value": 25.5}]
        expected_event = {"sensor_id": "temp_01", "value": 25.5, "publish_timestamp": 1234567890.0}

        publisher = SQSPublisher(queue_url=self.queue_url)

        # Act
        result = publisher.publish(events)

        # Assert
        self.assertIsInstance(result, PublishResult)
        self.assertEqual(result.successes, 1)
        self.assertEqual(result.failures, 0)
        self.assertEqual(result.retries, 0)
        
        mock_sqs.send_message.assert_called_once_with(
            QueueUrl=self.queue_url,
            MessageBody=json.dumps(expected_event, separators=(',', ':'))
        )

    @patch('boto3.client')
    @patch('time.time')
    def test_publish_multiple_events_success(self, mock_time, mock_boto_client):
        """Test successful multiple events publishing."""
        # Arrange
        mock_sqs = Mock()
        mock_boto_client.return_value = mock_sqs
        mock_time.return_value = 1234567890.0

        events = [
            {"sensor_id": "temp_01", "value": 25.5},
            {"sensor_id": "temp_02", "value": 26.0},
            {"sensor_id": "temp_03", "value": 24.8}
        ]

        publisher = SQSPublisher(queue_url=self.queue_url)

        # Act
        result = publisher.publish(events)

        # Assert
        self.assertEqual(result.successes, 3)
        self.assertEqual(result.failures, 0)
        self.assertEqual(result.retries, 0)
        self.assertEqual(mock_sqs.send_message.call_count, 3)

    @patch('boto3.client')
    @patch('time.sleep')
    def test_publish_single_event_with_retry_success(self, mock_sleep, mock_boto_client):
        """Test single event publishing with retry succeeding."""
        # Arrange
        mock_sqs = Mock()
        mock_boto_client.return_value = mock_sqs
        
        # First call fails, second succeeds
        mock_sqs.send_message.side_effect = [
            ClientError(
                error_response={'Error': {'Code': 'ServiceUnavailable'}},
                operation_name='SendMessage'
            ),
            None  # Success
        ]

        events = [{"sensor_id": "temp_01", "value": 25.5}]
        publisher = SQSPublisher(queue_url=self.queue_url)

        # Act
        result = publisher.publish(events)

        # Assert
        self.assertEqual(result.successes, 1)
        self.assertEqual(result.failures, 0)
        self.assertEqual(result.retries, 1)
        self.assertEqual(mock_sqs.send_message.call_count, 2)
        mock_sleep.assert_called_once()

    @patch('boto3.client')
    @patch('time.sleep')
    def test_publish_single_event_max_retries_exceeded(self, mock_sleep, mock_boto_client):
        """Test single event publishing with max retries exceeded."""
        # Arrange
        mock_sqs = Mock()
        mock_boto_client.return_value = mock_sqs
        
        # All calls fail
        mock_sqs.send_message.side_effect = ClientError(
            error_response={'Error': {'Code': 'ServiceUnavailable'}},
            operation_name='SendMessage'
        )

        events = [{"sensor_id": "temp_01", "value": 25.5}]
        publisher = SQSPublisher(queue_url=self.queue_url)

        # Act
        result = publisher.publish(events)

        # Assert
        self.assertEqual(result.successes, 0)
        self.assertEqual(result.failures, 1)
        self.assertEqual(result.retries, 4)  # 3 retries + 1 initial attempt
        self.assertEqual(mock_sqs.send_message.call_count, 4)
        self.assertEqual(mock_sleep.call_count, 3)

    @patch('boto3.client')
    def test_publish_mixed_success_failure(self, mock_boto_client):
        """Test publishing with mixed success and failure results."""
        # Arrange
        mock_sqs = Mock()
        mock_boto_client.return_value = mock_sqs
        
        # Use a counter to simulate different outcomes
        call_counter = {'count': 0}
        
        def send_message_side_effect(*args, **kwargs):
            call_counter['count'] += 1
            if call_counter['count'] == 1:
                return None  # First call succeeds
            else:
                # Subsequent calls fail (with retries)
                raise ClientError(
                    error_response={'Error': {'Code': 'ServiceUnavailable'}},
                    operation_name='SendMessage'
                )
        
        mock_sqs.send_message.side_effect = send_message_side_effect

        events = [
            {"sensor_id": "temp_01", "value": 25.5},
            {"sensor_id": "temp_02", "value": 26.0}
        ]
        publisher = SQSPublisher(queue_url=self.queue_url)

        # Act
        with patch('time.sleep'):  # Mock sleep to speed up test
            result = publisher.publish(events)

        # Assert
        self.assertEqual(result.successes, 1)
        self.assertEqual(result.failures, 1)
        self.assertGreater(result.retries, 0)

    @patch('boto3.client')
    def test_publish_empty_events_list(self, mock_boto_client):
        """Test publishing with empty events list."""
        # Arrange
        mock_sqs = Mock()
        mock_boto_client.return_value = mock_sqs

        publisher = SQSPublisher(queue_url=self.queue_url)

        # Act
        result = publisher.publish([])

        # Assert
        self.assertEqual(result.successes, 0)
        self.assertEqual(result.failures, 0)
        self.assertEqual(result.retries, 0)
        mock_sqs.send_message.assert_not_called()

    def test_close_method(self):
        """Test close method executes without error."""
        # Arrange
        publisher = SQSPublisher(queue_url=self.queue_url)

        # Act & Assert - should not raise exception
        publisher.close()


class TestBatchSQSPublisher(unittest.TestCase):
    """Test suite for BatchSQSPublisher class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.queue_url = "https://sqs.us-east-1.amazonaws.com/123456789/test-queue"
        self.region_name = "us-west-2"

    def test_initialization_success(self):
        """Test successful BatchSQSPublisher initialization."""
        # Act
        publisher = BatchSQSPublisher(
            queue_url=self.queue_url,
            region_name=self.region_name,
            batch_size=5,
            stream_interval=0.1
        )

        # Assert
        self.assertEqual(publisher.queue_url, self.queue_url)
        self.assertEqual(publisher.region_name, self.region_name)
        self.assertEqual(publisher.batch_size, 5)
        self.assertEqual(publisher.stream_interval, 0.1)

    def test_initialization_defaults(self):
        """Test BatchSQSPublisher initialization with default values."""
        # Act
        publisher = BatchSQSPublisher(queue_url=self.queue_url)

        # Assert
        self.assertEqual(publisher.batch_size, 10)
        self.assertEqual(publisher.stream_interval, 0.05)

    def test_initialization_batch_size_limit(self):
        """Test batch size is limited to AWS SQS constraint of 10."""
        # Act
        publisher = BatchSQSPublisher(
            queue_url=self.queue_url,
            batch_size=15  # Should be limited to 10
        )

        # Assert
        self.assertEqual(publisher.batch_size, 10)

    @patch('boto3.client')
    @patch('time.time')
    @patch('time.sleep')
    def test_publish_single_batch_success(self, mock_sleep, mock_time, mock_boto_client):
        """Test successful single batch publishing."""
        # Arrange
        mock_sqs = Mock()
        mock_boto_client.return_value = mock_sqs
        mock_time.return_value = 1234567890.0
        
        mock_sqs.send_message_batch.return_value = {
            'Successful': [{'Id': 'msg_0_0'}, {'Id': 'msg_0_1'}],
            'Failed': []
        }

        events = [
            {"sensor_id": "temp_01", "value": 25.5},
            {"sensor_id": "temp_02", "value": 26.0}
        ]

        publisher = BatchSQSPublisher(queue_url=self.queue_url, batch_size=5)
        mock_progress = Mock()

        # Act
        result = publisher.publish(events, progress_tracker=mock_progress)

        # Assert
        self.assertEqual(result.successes, 2)
        self.assertEqual(result.failures, 0)
        self.assertEqual(result.batches, 1)
        self.assertEqual(result.retries, 0)
        
        # Should not sleep for single batch
        mock_sleep.assert_not_called()
        
        # Progress tracker should be updated
        mock_progress.update.assert_called_with(2)
        mock_progress.set_postfix.assert_called()

    @patch('boto3.client')
    @patch('time.time')
    @patch('time.sleep')
    def test_publish_multiple_batches_success(self, mock_sleep, mock_time, mock_boto_client):
        """Test successful multiple batches publishing."""
        # Arrange
        mock_sqs = Mock()
        mock_boto_client.return_value = mock_sqs
        mock_time.return_value = 1234567890.0
        
        mock_sqs.send_message_batch.return_value = {
            'Successful': [{'Id': 'msg_0_0'}, {'Id': 'msg_0_1'}],
            'Failed': []
        }

        # 5 events with batch_size=2 should create 3 batches
        events = [
            {"sensor_id": f"temp_{i:02d}", "value": 25.0 + i}
            for i in range(5)
        ]

        publisher = BatchSQSPublisher(
            queue_url=self.queue_url,
            batch_size=2,
            stream_interval=0.01
        )

        # Act
        result = publisher.publish(events)

        # Assert
        self.assertEqual(result.successes, 5)
        self.assertEqual(result.failures, 0)
        self.assertEqual(result.batches, 3)  # ceil(5/2) = 3 batches
        self.assertEqual(mock_sqs.send_message_batch.call_count, 3)
        
        # Should sleep 2 times (between 3 batches)
        self.assertEqual(mock_sleep.call_count, 2)

    @patch('boto3.client')
    @patch('time.sleep')
    def test_publish_batch_with_partial_failure(self, mock_sleep, mock_boto_client):
        """Test batch publishing with partial failure."""
        # Arrange
        mock_sqs = Mock()
        mock_boto_client.return_value = mock_sqs
        
        mock_sqs.send_message_batch.return_value = {
            'Successful': [{'Id': 'msg_0_0'}],
            'Failed': [{'Id': 'msg_0_1', 'Code': 'InvalidMessage', 'Message': 'Test error'}]
        }

        events = [
            {"sensor_id": "temp_01", "value": 25.5},
            {"sensor_id": "temp_02", "value": 26.0}
        ]

        publisher = BatchSQSPublisher(queue_url=self.queue_url)

        # Act
        result = publisher.publish(events)

        # Assert
        self.assertEqual(result.successes, 0)  # Whole batch failed due to partial failure
        self.assertEqual(result.failures, 2)
        self.assertEqual(result.batches, 0)

    @patch('boto3.client')
    @patch('time.sleep')
    def test_publish_batch_with_retry_success(self, mock_sleep, mock_boto_client):
        """Test batch publishing with retry succeeding."""
        # Arrange
        mock_sqs = Mock()
        mock_boto_client.return_value = mock_sqs
        
        # First call fails, second succeeds
        mock_sqs.send_message_batch.side_effect = [
            ClientError(
                error_response={'Error': {'Code': 'ServiceUnavailable'}},
                operation_name='SendMessageBatch'
            ),
            {
                'Successful': [{'Id': 'msg_0_0'}],
                'Failed': []
            }
        ]

        events = [{"sensor_id": "temp_01", "value": 25.5}]
        publisher = BatchSQSPublisher(queue_url=self.queue_url)

        # Act
        result = publisher.publish(events)

        # Assert
        self.assertEqual(result.successes, 1)
        self.assertEqual(result.failures, 0)
        self.assertEqual(result.batches, 1)
        self.assertEqual(result.retries, 1)
        self.assertEqual(mock_sqs.send_message_batch.call_count, 2)

    @patch('boto3.client')
    @patch('time.sleep')
    def test_publish_batch_max_retries_exceeded(self, mock_sleep, mock_boto_client):
        """Test batch publishing with max retries exceeded."""
        # Arrange
        mock_sqs = Mock()
        mock_boto_client.return_value = mock_sqs
        
        # All calls fail
        mock_sqs.send_message_batch.side_effect = ClientError(
            error_response={'Error': {'Code': 'ServiceUnavailable'}},
            operation_name='SendMessageBatch'
        )

        events = [{"sensor_id": "temp_01", "value": 25.5}]
        publisher = BatchSQSPublisher(queue_url=self.queue_url)

        # Act
        result = publisher.publish(events)

        # Assert
        self.assertEqual(result.successes, 0)
        self.assertEqual(result.failures, 1)
        self.assertEqual(result.batches, 0)
        self.assertEqual(result.retries, 4)  # 3 retries + 1 initial attempt
        self.assertEqual(mock_sqs.send_message_batch.call_count, 4)

    @patch('boto3.client')
    @patch('time.time')
    def test_batch_entry_creation(self, mock_time, mock_boto_client):
        """Test batch entry creation with correct format."""
        # Arrange
        mock_sqs = Mock()
        mock_boto_client.return_value = mock_sqs
        mock_time.return_value = 1234567890.0
        
        mock_sqs.send_message_batch.return_value = {
            'Successful': [{'Id': 'msg_0_0'}],
            'Failed': []
        }

        events = [{"sensor_id": "temp_01", "value": 25.5}]
        publisher = BatchSQSPublisher(queue_url=self.queue_url)

        # Act
        publisher.publish(events)

        # Assert
        expected_entry = {
            'Id': 'msg_0_0',
            'MessageBody': json.dumps(
                {"sensor_id": "temp_01", "value": 25.5, "publish_timestamp": 1234567890.0},
                separators=(',', ':')
            )
        }
        
        mock_sqs.send_message_batch.assert_called_once_with(
            QueueUrl=self.queue_url,
            Entries=[expected_entry]
        )

    @patch('boto3.client')
    def test_publish_empty_events_batch(self, mock_boto_client):
        """Test batch publishing with empty events list."""
        # Arrange
        mock_sqs = Mock()
        mock_boto_client.return_value = mock_sqs

        publisher = BatchSQSPublisher(queue_url=self.queue_url)

        # Act
        result = publisher.publish([])

        # Assert
        self.assertEqual(result.successes, 0)
        self.assertEqual(result.failures, 0)
        self.assertEqual(result.batches, 0)
        self.assertEqual(result.retries, 0)
        mock_sqs.send_message_batch.assert_not_called()

    @patch('boto3.client')
    def test_publish_without_progress_tracker(self, mock_boto_client):
        """Test batch publishing without progress tracker."""
        # Arrange
        mock_sqs = Mock()
        mock_boto_client.return_value = mock_sqs
        
        mock_sqs.send_message_batch.return_value = {
            'Successful': [{'Id': 'msg_0_0'}],
            'Failed': []
        }

        events = [{"sensor_id": "temp_01", "value": 25.5}]
        publisher = BatchSQSPublisher(queue_url=self.queue_url)

        # Act & Assert - should not raise exception
        result = publisher.publish(events, progress_tracker=None)
        
        # Assert
        self.assertEqual(result.successes, 1)

    @patch('boto3.client')
    def test_publish_with_progress_tracker_on_failure(self, mock_boto_client):
        """Test batch publishing with progress tracker on failure."""
        # Arrange
        mock_sqs = Mock()
        mock_boto_client.return_value = mock_sqs
        
        mock_sqs.send_message_batch.return_value = {
            'Successful': [],
            'Failed': [{'Id': 'msg_0_0', 'Code': 'InvalidMessage'}]
        }

        events = [{"sensor_id": "temp_01", "value": 25.5}]
        publisher = BatchSQSPublisher(queue_url=self.queue_url)
        mock_progress = Mock()

        # Act
        result = publisher.publish(events, progress_tracker=mock_progress)

        # Assert
        self.assertEqual(result.failures, 1)
        # Progress tracker should still be updated on failures
        mock_progress.update.assert_called_with(1)
        mock_progress.set_postfix.assert_called()


if __name__ == '__main__':
    unittest.main(verbosity=2)
