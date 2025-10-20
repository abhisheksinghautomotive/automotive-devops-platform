"""Unit tests for SQS manager module."""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def setup_project_path():
    """Add project root to Python path for module imports."""
    project_root = Path(__file__).parent.parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))


# Setup path before importing project modules
setup_project_path()

from projects.can_data_platform.src.sqs.config import SQSQueueConfig  # noqa: E402
from projects.can_data_platform.src.sqs.manager import SQSQueueManager  # noqa: E402


class TestSQSQueueManager:
    """Test cases for SQSQueueManager class."""

    @pytest.fixture
    def config(self):
        """Create a test SQS configuration."""
        return SQSQueueConfig(
            queue_name="test-queue", region="us-east-1", visibility_timeout=30
        )

    @pytest.fixture
    def manager(self, config):
        """Create a test SQS manager with mocked boto3 session."""
        with patch('boto3.Session') as mock_session:
            mock_sqs = MagicMock()
            mock_session.return_value.client.return_value = mock_sqs
            manager = SQSQueueManager(config)
            manager.sqs = mock_sqs  # Direct assignment for testing
            return manager

    def test_init(self, config):
        """Test SQSQueueManager initialization."""
        with patch('boto3.Session') as mock_session:
            mock_sqs = MagicMock()
            mock_session.return_value.client.return_value = mock_sqs

            manager = SQSQueueManager(config)

            assert manager.config == config
            mock_session.assert_called_once_with(region_name="us-east-1")
            mock_session.return_value.client.assert_called_once_with("sqs")

    def test_init_with_profile(self, config):
        """Test SQSQueueManager initialization with AWS profile."""
        with patch('boto3.Session') as mock_session:
            mock_sqs = MagicMock()
            mock_session.return_value.client.return_value = mock_sqs

            manager = SQSQueueManager(config, profile="test-profile")

            assert manager.config == config
            mock_session.assert_called_once_with(
                region_name="us-east-1", profile_name="test-profile"
            )
            mock_session.return_value.client.assert_called_once_with("sqs")

    def test_create_queue_success(self, manager, config):
        """Test successful queue creation."""
        # Mock successful queue creation
        expected_queue_url = (
            "https://sqs.us-east-1.amazonaws.com/123456789012/test-queue"
        )
        manager.sqs.create_queue.return_value = {'QueueUrl': expected_queue_url}

        queue_url = manager.create_queue()

        # Verify the create_queue call
        manager.sqs.create_queue.assert_called_once_with(
            QueueName="test-queue",
            Attributes={
                'MessageRetentionPeriod': str(config.message_retention_seconds),
                'VisibilityTimeout': str(config.visibility_timeout),
                'ReceiveMessageWaitTimeSeconds': str(config.wait_time_seconds),
                'MaximumMessageSize': str(config.max_message_size),
            },
        )
        assert queue_url == expected_queue_url

    def test_create_queue_with_encryption(self, config):
        """Test queue creation with encryption enabled."""
        config.encrypt = True

        with patch('boto3.Session') as mock_session:
            mock_sqs = MagicMock()
            mock_session.return_value.client.return_value = mock_sqs
            manager = SQSQueueManager(config)
            manager.sqs = mock_sqs

            expected_queue_url = (
                "https://sqs.us-east-1.amazonaws.com/123456789012/test-queue"
            )
            mock_sqs.create_queue.return_value = {'QueueUrl': expected_queue_url}

            manager.create_queue()

        # Verify encryption is included in attributes
        call_args = mock_sqs.create_queue.call_args
        attributes = call_args[1]['Attributes']
        assert 'SqsManagedSseEnabled' in attributes
        assert attributes['SqsManagedSseEnabled'] == 'true'

    def test_create_queue_exception(self, manager):
        """Test queue creation with exception handling."""
        # Mock exception during queue creation
        from botocore.exceptions import ClientError

        error_response = {
            'Error': {
                'Code': 'QueueAlreadyExists',
                'Message': 'A queue already exists with the same name',
            }
        }
        manager.sqs.create_queue.side_effect = ClientError(
            error_response, 'CreateQueue'
        )

        with pytest.raises(ClientError):
            manager.create_queue()

    def test_send_test_message_success(self, manager):
        """Test successful test message sending."""
        queue_url = "https://sqs.us-east-1.amazonaws.com/123456789012/test-queue"
        test_payload = {"test": "data", "timestamp": "2023-01-01T00:00:00Z"}

        # Mock successful message send
        expected_response = {
            'MessageId': 'test-message-id-123',
            'MD5OfBody': 'test-md5-hash',
        }
        manager.sqs.send_message.return_value = expected_response

        result = manager.send_test_message(queue_url, test_payload)

        # Verify the send_message call
        manager.sqs.send_message.assert_called_once_with(
            QueueUrl=queue_url, MessageBody=json.dumps(test_payload)
        )
        assert result == expected_response

    def test_send_test_message_default_payload(self, manager):
        """Test sending test message with explicit payload."""
        queue_url = "https://sqs.us-east-1.amazonaws.com/123456789012/test-queue"
        test_payload = {"test": "SQS connectivity check", "from": "can-data-platform"}

        expected_response = {'MessageId': 'test-message-id-456'}
        manager.sqs.send_message.return_value = expected_response

        manager.send_test_message(queue_url, test_payload)

        # Verify payload is used
        call_args = manager.sqs.send_message.call_args
        message_body = json.loads(call_args[1]['MessageBody'])
        assert message_body['test'] == 'SQS connectivity check'
        assert message_body['from'] == 'can-data-platform'

    def test_receive_test_message_success(self, manager):
        """Test successful test message receiving."""
        queue_url = "https://sqs.us-east-1.amazonaws.com/123456789012/test-queue"

        # Mock successful message receive
        expected_response = {
            'Messages': [
                {
                    'MessageId': 'test-message-id-123',
                    'ReceiptHandle': 'test-receipt-handle',
                    'Body': '{"test": "data"}',
                }
            ]
        }
        manager.sqs.receive_message.return_value = expected_response

        result = manager.receive_test_message(queue_url)

        # Verify the receive_message call (uses config wait_time_seconds which is 20)
        manager.sqs.receive_message.assert_called_once_with(
            QueueUrl=queue_url, MaxNumberOfMessages=1, WaitTimeSeconds=20
        )
        assert result == expected_response

    def test_receive_test_message_no_messages(self, manager):
        """Test receiving when no messages are available."""
        queue_url = "https://sqs.us-east-1.amazonaws.com/123456789012/test-queue"

        # Mock empty response
        expected_response = {}
        manager.sqs.receive_message.return_value = expected_response

        result = manager.receive_test_message(queue_url)

        assert result == expected_response
        assert 'Messages' not in result
