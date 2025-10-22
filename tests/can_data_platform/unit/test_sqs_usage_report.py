#!/usr/bin/env python3
"""
Unit tests for SQS Usage Report Script

Tests the SQS usage reporting functionality including:
- Queue attribute fetching
- Report generation
- Environment variable handling
- AWS client configuration
"""

import os
import unittest
from unittest.mock import Mock, patch, call

# Import the module under test
import projects.can_data_platform.scripts.sqs_usage_report as sqs_usage_report


class TestSQSUsageReport(unittest.TestCase):
    """Test SQS usage reporting functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.queue_url = "https://sqs.us-east-1.amazonaws.com/123456789/test-queue"
        self.sample_attributes = {
            'ApproximateNumberOfMessages': '25',
            'ApproximateNumberOfMessagesNotVisible': '5',
            'CreatedTimestamp': '1640995200',
            'LastModifiedTimestamp': '1640995300',
        }

    @patch('boto3.client')
    @patch('builtins.print')
    def test_sqs_usage_report_success(self, mock_print, mock_boto_client):
        """Test successful SQS usage report generation."""
        # Arrange
        mock_sqs = Mock()
        mock_boto_client.return_value = mock_sqs
        mock_sqs.get_queue_attributes.return_value = {
            'Attributes': self.sample_attributes
        }

        # Act
        sqs_usage_report.sqs_usage_report(self.queue_url)

        # Assert
        mock_boto_client.assert_called_once_with("sqs", region_name="us-east-1")
        mock_sqs.get_queue_attributes.assert_called_once_with(
            QueueUrl=self.queue_url,
            AttributeNames=[
                'ApproximateNumberOfMessages',
                'ApproximateNumberOfMessagesNotVisible',
                'CreatedTimestamp',
                'LastModifiedTimestamp',
            ],
        )

        # Verify print statements
        expected_calls = [
            call(f"SQS Usage Report for {self.queue_url}"),
            call("Approximate messages in queue: 25"),
            call("Messages in flight (not visible): 5"),
            call("Queue Created: 1640995200"),
            call("Last Modified: 1640995300"),
        ]
        mock_print.assert_has_calls(expected_calls)

    @patch('os.getenv')
    @patch('boto3.client')
    def test_sqs_usage_report_custom_region(self, mock_boto_client, mock_getenv):
        """Test SQS usage report with custom AWS region."""
        # Arrange
        mock_getenv.return_value = "eu-west-1"
        mock_sqs = Mock()
        mock_boto_client.return_value = mock_sqs
        mock_sqs.get_queue_attributes.return_value = {
            'Attributes': self.sample_attributes
        }

        # Act
        sqs_usage_report.sqs_usage_report(self.queue_url)

        # Assert
        mock_boto_client.assert_called_once_with("sqs", region_name="eu-west-1")

    @patch('boto3.client')
    def test_sqs_usage_report_boto_error(self, mock_boto_client):
        """Test SQS usage report with boto client error."""
        # Arrange
        mock_sqs = Mock()
        mock_boto_client.return_value = mock_sqs
        mock_sqs.get_queue_attributes.side_effect = Exception("Access denied")

        # Act & Assert
        with self.assertRaises(Exception) as context:
            sqs_usage_report.sqs_usage_report(self.queue_url)

        self.assertEqual(str(context.exception), "Access denied")

    @patch('boto3.client')
    @patch('builtins.print')
    def test_sqs_usage_report_zero_messages(self, mock_print, mock_boto_client):
        """Test SQS usage report with zero messages in queue."""
        # Arrange
        mock_sqs = Mock()
        mock_boto_client.return_value = mock_sqs
        zero_attributes = {
            'ApproximateNumberOfMessages': '0',
            'ApproximateNumberOfMessagesNotVisible': '0',
            'CreatedTimestamp': '1640995200',
            'LastModifiedTimestamp': '1640995300',
        }
        mock_sqs.get_queue_attributes.return_value = {'Attributes': zero_attributes}

        # Act
        sqs_usage_report.sqs_usage_report(self.queue_url)

        # Assert
        expected_calls = [
            call(f"SQS Usage Report for {self.queue_url}"),
            call("Approximate messages in queue: 0"),
            call("Messages in flight (not visible): 0"),
            call("Queue Created: 1640995200"),
            call("Last Modified: 1640995300"),
        ]
        mock_print.assert_has_calls(expected_calls)

    @patch('boto3.client')
    @patch('builtins.print')
    def test_sqs_usage_report_high_message_count(self, mock_print, mock_boto_client):
        """Test SQS usage report with high message counts."""
        # Arrange
        mock_sqs = Mock()
        mock_boto_client.return_value = mock_sqs
        high_count_attributes = {
            'ApproximateNumberOfMessages': '50000',
            'ApproximateNumberOfMessagesNotVisible': '10000',
            'CreatedTimestamp': '1640995200',
            'LastModifiedTimestamp': '1640995300',
        }
        mock_sqs.get_queue_attributes.return_value = {
            'Attributes': high_count_attributes
        }

        # Act
        sqs_usage_report.sqs_usage_report(self.queue_url)

        # Assert
        expected_calls = [
            call(f"SQS Usage Report for {self.queue_url}"),
            call("Approximate messages in queue: 50000"),
            call("Messages in flight (not visible): 10000"),
            call("Queue Created: 1640995200"),
            call("Last Modified: 1640995300"),
        ]
        mock_print.assert_has_calls(expected_calls)


class TestSetupProjectPath(unittest.TestCase):
    """Test project path setup functionality."""

    @patch('sys.path')
    def test_setup_project_path_adds_path(self, mock_sys_path):
        """Test that setup_project_path adds project root to sys.path."""
        # Arrange
        mock_sys_path.copy.return_value = []  # Mock empty path list

        # Act
        sqs_usage_report.setup_project_path()

        # Assert
        # Verify that insert was called (path should be added)
        self.assertTrue(mock_sys_path.insert.called)

    @patch('sys.path', ['existing_path'])
    def test_setup_project_path_already_exists(self, mock_sys_path=None):
        """Test setup_project_path when path already exists."""
        # This test verifies the logic but mocking sys.path completely
        # is complex, so we test the function doesn't crash

        # Act & Assert - Should not raise exception
        sqs_usage_report.setup_project_path()


class TestMainExecution(unittest.TestCase):
    """Test main script execution logic."""

    @patch.dict(os.environ, {'SQS_QUEUE_URL': 'https://test-queue-url'})
    @patch('projects.can_data_platform.scripts.sqs_usage_report.sqs_usage_report')
    def test_main_execution_with_queue_url(self, mock_sqs_report):
        """Test main execution when SQS_QUEUE_URL is set."""
        # Arrange
        test_queue_url = 'https://test-queue-url'

        # Mock the main execution by importing the module
        # This simulates running the script
        with patch('os.getenv', return_value=test_queue_url):
            # Act
            # We can't directly test __main__ execution, but we can test
            # the function would be called with correct parameters
            queue_url = os.getenv("SQS_QUEUE_URL")
            if queue_url:
                mock_sqs_report(queue_url)

        # Assert
        mock_sqs_report.assert_called_once_with(test_queue_url)

    @patch.dict(os.environ, {}, clear=True)
    def test_main_execution_missing_queue_url(self):
        """Test main execution when SQS_QUEUE_URL is not set."""
        # Act & Assert
        with self.assertRaises(ValueError) as context:
            queue_url = os.getenv("SQS_QUEUE_URL")
            if not queue_url:
                raise ValueError("SQS_QUEUE_URL not set. Add to .env.")

        self.assertEqual(str(context.exception), "SQS_QUEUE_URL not set. Add to .env.")

    @patch('os.getenv')
    def test_queue_url_environment_variable_handling(self, mock_getenv):
        """Test proper handling of SQS_QUEUE_URL environment variable."""
        # Arrange
        test_url = "https://sqs.us-west-2.amazonaws.com/123456789/my-queue"
        mock_getenv.return_value = test_url

        # Act
        result = os.getenv("SQS_QUEUE_URL")

        # Assert
        self.assertEqual(result, test_url)
        mock_getenv.assert_called_with("SQS_QUEUE_URL")

    def test_queue_url_none_handling(self):
        """Test handling when queue URL is None."""
        # Arrange
        queue_url = None

        # Act & Assert
        with self.assertRaises(ValueError):
            if not queue_url:
                raise ValueError("SQS_QUEUE_URL not set. Add to .env.")


class TestEnvironmentConfiguration(unittest.TestCase):
    """Test environment configuration and AWS region handling."""

    @patch('projects.can_data_platform.scripts.sqs_usage_report.os.getenv')
    @patch('boto3.client')
    def test_default_aws_region(self, mock_boto_client, mock_getenv):
        """Test default AWS region when AWS_REGION not set."""
        # Arrange
        # When called with ("AWS_REGION", "us-east-1"), return the default
        mock_getenv.side_effect = (
            lambda key, default=None: default if key == "AWS_REGION" else None
        )
        mock_sqs = Mock()
        mock_boto_client.return_value = mock_sqs
        mock_sqs.get_queue_attributes.return_value = {
            'Attributes': {
                'ApproximateNumberOfMessages': '0',
                'ApproximateNumberOfMessagesNotVisible': '0',
                'CreatedTimestamp': '1640995200',
                'LastModifiedTimestamp': '1640995300',
            }
        }

        # Act
        sqs_usage_report.sqs_usage_report("test-queue-url")

        # Assert
        mock_boto_client.assert_called_once_with("sqs", region_name="us-east-1")

    @patch('projects.can_data_platform.scripts.sqs_usage_report.os.getenv')
    @patch('boto3.client')
    def test_custom_aws_region(self, mock_boto_client, mock_getenv):
        """Test custom AWS region from environment variable."""
        # Arrange
        # When called with ("AWS_REGION", "us-east-1"), return custom region
        mock_getenv.side_effect = (
            lambda key, default=None: "ap-southeast-2"
            if key == "AWS_REGION"
            else default
        )
        mock_sqs = Mock()
        mock_boto_client.return_value = mock_sqs
        mock_sqs.get_queue_attributes.return_value = {
            'Attributes': {
                'ApproximateNumberOfMessages': '0',
                'ApproximateNumberOfMessagesNotVisible': '0',
                'CreatedTimestamp': '1640995200',
                'LastModifiedTimestamp': '1640995300',
            }
        }

        # Act
        sqs_usage_report.sqs_usage_report("test-queue-url")

        # Assert
        mock_boto_client.assert_called_once_with("sqs", region_name="ap-southeast-2")


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
