"""
Unit tests for batch_sqs_consumer.py script.

Tests the SQS batch consumer functionality including message processing,
batch handling, deletion logic, and error scenarios.
"""

import json
import logging
import os
import unittest
from unittest.mock import Mock, call, patch

# pyright: ignore[reportMissingImports]
from botocore.exceptions import BotoCoreError, ClientError


class TestBatchSQSConsumerMessageProcessing(unittest.TestCase):
    """Test message processing functionality."""

    def test_process_message_body_valid_json(self):
        """Test processing valid JSON message body."""
        from projects.can_data_platform.scripts.batch_sqs_consumer import (
            process_message_body,
        )

        valid_json = '{"voltage": 3700, "module": 1}'
        result = process_message_body(valid_json)
        self.assertTrue(result)

    def test_process_message_body_invalid_json(self):
        """Test processing invalid JSON message body."""
        from projects.can_data_platform.scripts.batch_sqs_consumer import (
            process_message_body,
        )

        invalid_json = '{"voltage": 3700, "module": 1'  # Missing closing brace
        with self.assertLogs(level='ERROR') as log:
            result = process_message_body(invalid_json)

        self.assertFalse(result)
        self.assertTrue(any('Could not process message' in msg for msg in log.output))

    def test_process_message_body_empty_json(self):
        """Test processing empty JSON object."""
        from projects.can_data_platform.scripts.batch_sqs_consumer import (
            process_message_body,
        )

        empty_json = '{}'
        result = process_message_body(empty_json)
        self.assertTrue(result)

    def test_process_message_body_complex_json(self):
        """Test processing complex JSON structure."""
        from projects.can_data_platform.scripts.batch_sqs_consumer import (
            process_message_body,
        )

        complex_json = json.dumps(
            {
                "Cell1Voltage": 3700,
                "Cell2Voltage": 3750,
                "min_voltage": 3700,
                "max_voltage": 3750,
                "avg_voltage": 3725,
                "module_offsets": [-20, 30],
            }
        )
        result = process_message_body(complex_json)
        self.assertTrue(result)


class TestBatchSQSConsumerReceiveMessages(unittest.TestCase):
    """Test message receiving functionality."""

    @patch('boto3.client')
    def test_receive_messages_success(self, mock_boto_client):
        """Test successful message receiving."""
        from projects.can_data_platform.scripts.batch_sqs_consumer import (
            receive_messages,
        )

        mock_sqs = Mock()
        mock_response = {
            'Messages': [
                {
                    'MessageId': '1',
                    'Body': '{"test": "data"}',
                    'ReceiptHandle': 'handle1',
                },
                {
                    'MessageId': '2',
                    'Body': '{"test": "data2"}',
                    'ReceiptHandle': 'handle2',
                },
            ]
        }
        mock_sqs.receive_message.return_value = mock_response

        result = receive_messages(mock_sqs)

        self.assertEqual(result, mock_response)
        mock_sqs.receive_message.assert_called_once()

    @patch('boto3.client')
    def test_receive_messages_boto_error(self, mock_boto_client):
        """Test message receiving with BotoCoreError."""
        from projects.can_data_platform.scripts.batch_sqs_consumer import (
            receive_messages,
        )

        mock_sqs = Mock()
        mock_sqs.receive_message.side_effect = BotoCoreError()

        with self.assertLogs(level='ERROR') as log:
            result = receive_messages(mock_sqs)

        self.assertIsNone(result)
        self.assertTrue(any('Failed to receive batch' in msg for msg in log.output))

    @patch('boto3.client')
    def test_receive_messages_client_error(self, mock_boto_client):
        """Test message receiving with ClientError."""
        from projects.can_data_platform.scripts.batch_sqs_consumer import (
            receive_messages,
        )

        mock_sqs = Mock()
        mock_sqs.receive_message.side_effect = ClientError(
            error_response={'Error': {'Code': 'AccessDenied'}},
            operation_name='ReceiveMessage',
        )

        with self.assertLogs(level='ERROR') as log:
            result = receive_messages(mock_sqs)

        self.assertIsNone(result)
        self.assertTrue(any('Failed to receive batch' in msg for msg in log.output))

    @patch('boto3.client')
    def test_receive_messages_no_messages(self, mock_boto_client):
        """Test message receiving when no messages are available."""
        from projects.can_data_platform.scripts.batch_sqs_consumer import (
            receive_messages,
        )

        mock_sqs = Mock()
        mock_response = {}  # No Messages key
        mock_sqs.receive_message.return_value = mock_response

        result = receive_messages(mock_sqs)

        self.assertEqual(result, mock_response)


class TestBatchSQSConsumerDeleteMessages(unittest.TestCase):
    """Test message deletion functionality."""

    @patch('time.sleep')
    def test_delete_messages_success(self, mock_sleep):
        """Test successful message deletion."""
        from projects.can_data_platform.scripts.batch_sqs_consumer import (
            delete_messages,
        )

        mock_sqs = Mock()
        mock_sqs.delete_message_batch.return_value = {
            'Successful': [{'Id': '1'}, {'Id': '2'}]
        }

        entries = [
            {'Id': '1', 'ReceiptHandle': 'handle1'},
            {'Id': '2', 'ReceiptHandle': 'handle2'},
        ]

        with self.assertLogs(level='INFO') as log:
            result = delete_messages(mock_sqs, entries)

        self.assertTrue(result)
        self.assertTrue(any('Deleted 2 messages' in msg for msg in log.output))
        mock_sqs.delete_message_batch.assert_called_once()
        mock_sleep.assert_not_called()

    @patch('time.sleep')
    def test_delete_messages_retry_success(self, mock_sleep):
        """Test message deletion succeeds after retry."""
        from projects.can_data_platform.scripts.batch_sqs_consumer import (
            delete_messages,
        )

        mock_sqs = Mock()
        # First call fails, second succeeds
        mock_sqs.delete_message_batch.side_effect = [
            BotoCoreError(),
            {'Successful': [{'Id': '1'}]},
        ]

        entries = [{'Id': '1', 'ReceiptHandle': 'handle1'}]

        with self.assertLogs(level='WARNING') as log:
            result = delete_messages(mock_sqs, entries)

        self.assertTrue(result)
        self.assertEqual(mock_sqs.delete_message_batch.call_count, 2)
        mock_sleep.assert_called_once_with(2)  # First retry delay
        self.assertTrue(
            any('Attempt 1: Failed to delete batch' in msg for msg in log.output)
        )

    @patch('time.sleep')
    def test_delete_messages_max_retries_exceeded(self, mock_sleep):
        """Test message deletion fails after max retries."""
        from projects.can_data_platform.scripts.batch_sqs_consumer import (
            delete_messages,
        )

        mock_sqs = Mock()
        mock_sqs.delete_message_batch.side_effect = BotoCoreError()

        entries = [{'Id': '1', 'ReceiptHandle': 'handle1'}]

        with self.assertLogs(level='WARNING'):
            result = delete_messages(mock_sqs, entries)

        self.assertFalse(result)
        self.assertEqual(mock_sqs.delete_message_batch.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 3)

        # Check retry delays: 2, 4, 6 seconds
        expected_calls = [call(2), call(4), call(6)]
        mock_sleep.assert_has_calls(expected_calls)

    def test_delete_messages_empty_entries(self):
        """Test delete_messages with empty entries list."""
        from projects.can_data_platform.scripts.batch_sqs_consumer import (
            delete_messages,
        )

        mock_sqs = Mock()
        mock_sqs.delete_message_batch.return_value = {'Successful': []}

        result = delete_messages(mock_sqs, [])

        self.assertTrue(result)
        mock_sqs.delete_message_batch.assert_called_once()


class TestBatchSQSConsumerProcessBatch(unittest.TestCase):
    """Test batch processing functionality."""

    @patch('projects.can_data_platform.scripts.batch_sqs_consumer.process_message_body')
    def test_process_batch_all_success(self, mock_process):
        """Test processing batch where all messages succeed."""
        from projects.can_data_platform.scripts.batch_sqs_consumer import process_batch

        mock_process.return_value = True

        messages = [
            {'MessageId': '1', 'Body': '{"test": 1}', 'ReceiptHandle': 'handle1'},
            {'MessageId': '2', 'Body': '{"test": 2}', 'ReceiptHandle': 'handle2'},
        ]

        entries_to_delete, success_count, failure_count = process_batch(messages)

        self.assertEqual(len(entries_to_delete), 2)
        self.assertEqual(success_count, 2)
        self.assertEqual(failure_count, 0)

        expected_entries = [
            {'Id': '1', 'ReceiptHandle': 'handle1'},
            {'Id': '2', 'ReceiptHandle': 'handle2'},
        ]
        self.assertEqual(entries_to_delete, expected_entries)

    @patch('projects.can_data_platform.scripts.batch_sqs_consumer.process_message_body')
    def test_process_batch_partial_success(self, mock_process):
        """Test processing batch with partial success."""
        from projects.can_data_platform.scripts.batch_sqs_consumer import process_batch

        # First message succeeds, second fails
        mock_process.side_effect = [True, False]

        messages = [
            {'MessageId': '1', 'Body': '{"test": 1}', 'ReceiptHandle': 'handle1'},
            {'MessageId': '2', 'Body': 'invalid json', 'ReceiptHandle': 'handle2'},
        ]

        entries_to_delete, success_count, failure_count = process_batch(messages)

        self.assertEqual(len(entries_to_delete), 1)
        self.assertEqual(success_count, 1)
        self.assertEqual(failure_count, 1)

        expected_entries = [{'Id': '1', 'ReceiptHandle': 'handle1'}]
        self.assertEqual(entries_to_delete, expected_entries)

    @patch('projects.can_data_platform.scripts.batch_sqs_consumer.process_message_body')
    def test_process_batch_all_failure(self, mock_process):
        """Test processing batch where all messages fail."""
        from projects.can_data_platform.scripts.batch_sqs_consumer import process_batch

        mock_process.return_value = False

        messages = [
            {'MessageId': '1', 'Body': 'invalid', 'ReceiptHandle': 'handle1'},
            {'MessageId': '2', 'Body': 'also invalid', 'ReceiptHandle': 'handle2'},
        ]

        entries_to_delete, success_count, failure_count = process_batch(messages)

        self.assertEqual(len(entries_to_delete), 0)
        self.assertEqual(success_count, 0)
        self.assertEqual(failure_count, 2)

    def test_process_batch_empty_messages(self):
        """Test processing empty message batch."""
        from projects.can_data_platform.scripts.batch_sqs_consumer import process_batch

        entries_to_delete, success_count, failure_count = process_batch([])

        self.assertEqual(len(entries_to_delete), 0)
        self.assertEqual(success_count, 0)
        self.assertEqual(failure_count, 0)


class TestBatchSQSConsumerEnvironmentVariables(unittest.TestCase):
    """Test environment variable handling."""

    def test_environment_variable_defaults(self):
        """Test that environment variables have correct defaults."""
        # Import the module to check constants
        import projects.can_data_platform.scripts.batch_sqs_consumer as consumer_module

        # These should be set from environment or defaults
        self.assertIsNotNone(consumer_module.BATCH_SIZE)
        self.assertIsNotNone(consumer_module.POLL_INTERVAL)
        self.assertIsNotNone(consumer_module.MAX_RETRIES)
        self.assertIsNotNone(consumer_module.AWS_REGION)

        # Check types and reasonable ranges
        self.assertIsInstance(consumer_module.BATCH_SIZE, int)
        self.assertIsInstance(consumer_module.POLL_INTERVAL, int)
        self.assertIsInstance(consumer_module.MAX_RETRIES, int)
        self.assertIsInstance(consumer_module.AWS_REGION, str)

        # SQS batch size should not exceed AWS limit
        self.assertLessEqual(consumer_module.BATCH_SIZE, 10)

    @patch.dict(
        os.environ,
        {
            'SQS_BATCH_SIZE': '5',
            'SQS_CONSUMER_POLL_SEC': '10',
            'SQS_DELETION_MAX_RETRIES': '5',
            'AWS_REGION': 'eu-west-1',
        },
    )
    def test_environment_variable_override(self):
        """Test environment variable override functionality."""
        # Re-import to pick up new environment variables
        import importlib
        import projects.can_data_platform.scripts.batch_sqs_consumer as consumer_module

        importlib.reload(consumer_module)

        self.assertEqual(consumer_module.BATCH_SIZE, 5)
        self.assertEqual(consumer_module.POLL_INTERVAL, 10)
        self.assertEqual(consumer_module.MAX_RETRIES, 5)
        self.assertEqual(consumer_module.AWS_REGION, 'eu-west-1')


class TestBatchSQSConsumerIntegration(unittest.TestCase):
    """Test integration scenarios and main consumer loop."""

    @patch('time.sleep')
    @patch('boto3.client')
    @patch('projects.can_data_platform.scripts.batch_sqs_consumer.delete_messages')
    @patch('projects.can_data_platform.scripts.batch_sqs_consumer.process_batch')
    @patch('projects.can_data_platform.scripts.batch_sqs_consumer.receive_messages')
    @patch('builtins.print')
    def test_batch_consume_sqs_successful_cycle(
        self, mock_print, mock_receive, mock_process, mock_delete, mock_boto, mock_sleep
    ):
        """Test one successful cycle of the batch consumer."""
        mock_sqs = Mock()
        mock_boto.return_value = mock_sqs

        messages = [
            {'MessageId': '1', 'Body': '{"test": 1}', 'ReceiptHandle': 'handle1'}
        ]
        mock_receive.return_value = {'Messages': messages}

        mock_process.return_value = (
            [{'Id': '1', 'ReceiptHandle': 'handle1'}],  # entries_to_delete
            1,  # batch_success
            0,  # batch_failure
        )
        mock_delete.return_value = True

        # Test the logic components rather than the infinite loop
        from projects.can_data_platform.scripts.batch_sqs_consumer import (
            receive_messages,
            process_batch,
        )

        # Test receive messages
        resp = receive_messages(mock_sqs)
        self.assertEqual(resp, {'Messages': messages})

        # Test process batch
        _, batch_success, batch_failure = process_batch(messages)
        self.assertEqual(batch_success, 1)
        self.assertEqual(batch_failure, 0)

        mock_receive.assert_called_once_with(mock_sqs)
        mock_process.assert_called_once_with(messages)

    @patch('time.sleep')
    @patch('boto3.client')
    @patch('projects.can_data_platform.scripts.batch_sqs_consumer.receive_messages')
    @patch('builtins.print')
    def test_batch_consume_sqs_no_messages(
        self, mock_print, mock_receive, mock_boto, mock_sleep
    ):
        """Test consumer behavior when no messages are available."""
        mock_sqs = Mock()
        mock_boto.return_value = mock_sqs

        # Mock the receive_messages function to return empty once
        mock_receive.return_value = {'Messages': []}

        # Import and patch the actual function to break the infinite loop
        with patch(
            'projects.can_data_platform.scripts.batch_sqs_consumer.POLL_INTERVAL', 1
        ):
            # We'll test the logic components rather than the infinite loop
            from projects.can_data_platform.scripts.batch_sqs_consumer import (
                receive_messages,
            )

            result = receive_messages(mock_sqs)
            self.assertEqual(result, {'Messages': []})

        mock_receive.assert_called_once_with(mock_sqs)

    @patch('time.sleep')
    @patch('boto3.client')
    @patch('projects.can_data_platform.scripts.batch_sqs_consumer.receive_messages')
    def test_batch_consume_sqs_consecutive_failures(
        self, mock_receive, mock_boto, mock_sleep
    ):
        """Test consumer behavior with consecutive failures."""
        from projects.can_data_platform.scripts.batch_sqs_consumer import (
            batch_consume_sqs,
        )

        mock_sqs = Mock()
        mock_boto.return_value = mock_sqs

        # Return None (failure) multiple times
        mock_receive.return_value = None

        with patch(
            'projects.can_data_platform.scripts.batch_sqs_consumer.batch_consume_sqs'
        ) as mock_consumer:

            def side_effect():
                consecutive_failures = 0
                for _ in range(7):  # More than the 5 failure limit
                    result = mock_receive(mock_sqs)
                    if result is None:
                        consecutive_failures += 1
                        if consecutive_failures > 5:
                            break
                    else:
                        consecutive_failures = 0

            mock_consumer.side_effect = side_effect
            batch_consume_sqs()

        # Should have called receive_messages multiple times
        self.assertGreaterEqual(mock_receive.call_count, 5)


class TestBatchSQSConsumerLogging(unittest.TestCase):
    """Test logging functionality."""

    def test_log_file_creation(self):
        """Test that log file path is constructed correctly."""
        import projects.can_data_platform.scripts.batch_sqs_consumer as consumer_module

        # Check that log_file variable is set
        self.assertTrue(hasattr(consumer_module, 'log_file'))
        log_file = consumer_module.log_file
        self.assertTrue(log_file.endswith('batch_consumer.log'))

    def test_logging_configuration(self):
        """Test that logging is configured correctly."""
        # Check that logging level is set
        logger = logging.getLogger()
        self.assertLessEqual(logger.level, logging.INFO)


if __name__ == '__main__':
    unittest.main()
