"""Unit tests for TelemetryApp using comprehensive testing patterns."""

import unittest
from unittest.mock import Mock, patch

from projects.can_data_platform.src.apps.telemetry_app import TelemetryApp
from projects.can_data_platform.src.config import TelemetryConfig
from projects.can_data_platform.src.events import EventGenerator
from projects.can_data_platform.src.file_operations import FileWriter
from projects.can_data_platform.src.publishers import PublisherInterface
from projects.can_data_platform.src.tracking import ProgressTracker


class TestTelemetryApp(unittest.TestCase):
    """Test cases for TelemetryApp class."""

    def setUp(self):
        """Set up test fixtures for each test method."""
        # Mock dependencies
        self.mock_config = Mock(spec=TelemetryConfig)
        self.mock_config.default_output_path = "/tmp/test_output.jsonl"
        self.mock_config.sqs_queue_url = "https://sqs.us-east-1.amazonaws.com/123456789012/test-queue"

        self.mock_event_generator = Mock(spec=EventGenerator)
        self.mock_file_writer = Mock(spec=FileWriter)
        self.mock_publisher = Mock(spec=PublisherInterface)
        self.mock_progress_tracker = Mock(spec=ProgressTracker)

        # Create app instance
        self.app = TelemetryApp(
            config=self.mock_config,
            event_generator=self.mock_event_generator,
            file_writer=self.mock_file_writer,
            publisher=self.mock_publisher,
            progress_tracker=self.mock_progress_tracker,
        )

    def test_initialization_success(self):
        """Test successful TelemetryApp initialization."""
        # Assert all dependencies are properly set
        self.assertEqual(self.app.config, self.mock_config)
        self.assertEqual(self.app.event_generator, self.mock_event_generator)
        self.assertEqual(self.app.file_writer, self.mock_file_writer)
        self.assertEqual(self.app.publisher, self.mock_publisher)
        self.assertEqual(self.app.progress_tracker, self.mock_progress_tracker)

    @patch('projects.can_data_platform.src.apps.telemetry_app.time.time')
    def test_generate_events_success(self, mock_time):
        """Test successful event generation with progress tracking."""
        # Arrange
        num_events = 5
        mock_time.side_effect = [1000.0, 1005.0]  # 5 second duration

        # Mock event objects with to_dict method
        mock_event_objs = []
        for i in range(num_events):
            mock_event = Mock()
            mock_event.to_dict.return_value = {"event_id": i, "data": f"test_data_{i}"}
            mock_event_objs.append(mock_event)

        self.mock_event_generator.generate_events.return_value = mock_event_objs

        # Act
        result = self.app.generate_events(num_events)

        # Assert
        self.assertEqual(len(result), num_events)
        for i, event in enumerate(result):
            self.assertEqual(event, {"event_id": i, "data": f"test_data_{i}"})

        # Verify progress tracking calls
        self.mock_progress_tracker.start.assert_called_once_with(num_events, "⚡ Generating Events")
        self.assertEqual(self.mock_progress_tracker.update.call_count, num_events)
        self.mock_progress_tracker.close.assert_called_once()

        # Verify event generator called correctly
        self.mock_event_generator.generate_events.assert_called_once_with(num_events)

    @patch('projects.can_data_platform.src.apps.telemetry_app.time.time')
    def test_generate_events_empty_list(self, mock_time):
        """Test event generation with zero events."""
        # Arrange
        num_events = 0
        mock_time.side_effect = [1000.0, 1000.1]
        self.mock_event_generator.generate_events.return_value = []

        # Act
        result = self.app.generate_events(num_events)

        # Assert
        self.assertEqual(result, [])
        self.mock_progress_tracker.start.assert_called_once_with(0, "⚡ Generating Events")
        self.mock_progress_tracker.update.assert_not_called()
        self.mock_progress_tracker.close.assert_called_once()

    def test_publish_to_file_success(self):
        """Test successful file publishing."""
        # Arrange
        events = [{"id": 1, "data": "test"}]
        output_path = "/tmp/test.jsonl"

        # Act
        self.app.publish_to_file(events, output_path)

        # Assert
        self.mock_file_writer.write.assert_called_once_with(events, output_path)

    def test_publish_to_file_io_error(self):
        """Test file publishing with IO error."""
        # Arrange
        events = [{"id": 1, "data": "test"}]
        output_path = "/tmp/test.jsonl"
        self.mock_file_writer.write.side_effect = IOError("Permission denied")

        # Act & Assert
        with self.assertRaises(IOError):
            self.app.publish_to_file(events, output_path)

        self.mock_file_writer.write.assert_called_once_with(events, output_path)

    def test_publish_to_file_os_error(self):
        """Test file publishing with OS error."""
        # Arrange
        events = [{"id": 1, "data": "test"}]
        output_path = "/tmp/test.jsonl"
        self.mock_file_writer.write.side_effect = OSError("Disk full")

        # Act & Assert
        with self.assertRaises(OSError):
            self.app.publish_to_file(events, output_path)

    @patch('projects.can_data_platform.src.apps.telemetry_app.time.time')
    def test_publish_to_sqs_success(self, mock_time):
        """Test successful SQS publishing with progress tracking."""
        # Arrange
        events = [{"id": 1}, {"id": 2}]
        mock_time.side_effect = [2000.0, 2005.0]  # 5 second duration

        # Mock publisher result
        mock_result = Mock()
        mock_result.successes = 2
        mock_result.failures = 0
        mock_result.batches = 1
        mock_result.retries = 0
        mock_result.success_rate = 100.0
        self.mock_publisher.publish.return_value = mock_result

        # Act
        result = self.app.publish_to_sqs(events)

        # Assert
        expected_result = {
            "successes": 2,
            "failures": 0,
            "batches": 1,
            "retries": 0,
        }
        self.assertEqual(result, expected_result)

        # Verify progress tracking
        self.mock_progress_tracker.start.assert_called_once_with(2, "📡 Publishing to SQS")
        self.mock_progress_tracker.set_postfix.assert_called_once()
        self.mock_progress_tracker.close.assert_called_once()

        # Verify publisher called with progress tracker
        self.mock_publisher.publish.assert_called_once_with(events, self.mock_progress_tracker)

    @patch('projects.can_data_platform.src.apps.telemetry_app.time.time')
    def test_publish_to_sqs_with_failures(self, mock_time):
        """Test SQS publishing with some failures."""
        # Arrange
        events = [{"id": 1}, {"id": 2}, {"id": 3}]
        mock_time.side_effect = [2000.0, 2003.0]

        mock_result = Mock()
        mock_result.successes = 2
        mock_result.failures = 1
        mock_result.batches = 1
        mock_result.retries = 3
        mock_result.success_rate = 66.7
        self.mock_publisher.publish.return_value = mock_result

        # Act
        result = self.app.publish_to_sqs(events)

        # Assert
        expected_result = {
            "successes": 2,
            "failures": 1,
            "batches": 1,
            "retries": 3,
        }
        self.assertEqual(result, expected_result)

    def test_publish_to_sqs_exception(self):
        """Test SQS publishing with exception handling."""
        # Arrange
        events = [{"id": 1}]
        self.mock_publisher.publish.side_effect = Exception("SQS connection failed")

        # Act & Assert
        with self.assertRaises(Exception):
            self.app.publish_to_sqs(events)

        # Verify progress tracker is closed on exception
        self.mock_progress_tracker.close.assert_called_once()

    def test_run_file_mode(self):
        """Test run method in file mode."""
        # Arrange
        num_events = 3
        mode = "file"
        output_path = "/tmp/test.jsonl"

        # Mock event generation
        mock_events = [{"id": 1}, {"id": 2}, {"id": 3}]
        with patch.object(self.app, 'generate_events', return_value=mock_events) as mock_gen:
            with patch.object(self.app, 'publish_to_file') as mock_pub_file:
                # Act
                result = self.app.run(num_events, mode, output_path)

                # Assert
                self.assertTrue(result["file_written"])
                self.assertIn("total_execution_time", result)
                self.assertIsInstance(result["total_execution_time"], float)

                mock_gen.assert_called_once_with(num_events)
                mock_pub_file.assert_called_once_with(mock_events, output_path)
                self.mock_publisher.close.assert_called_once()

    def test_run_sqs_mode(self):
        """Test run method in SQS mode."""
        # Arrange
        num_events = 2
        mode = "sqs"

        mock_events = [{"id": 1}, {"id": 2}]
        sqs_stats = {"successes": 2, "failures": 0, "batches": 1, "retries": 0}

        with patch.object(self.app, 'generate_events', return_value=mock_events) as mock_gen:
            with patch.object(self.app, 'publish_to_sqs', return_value=sqs_stats) as mock_pub_sqs:
                # Act
                result = self.app.run(num_events, mode)

                # Assert
                expected_result = {
                    "successes": 2,
                    "failures": 0,
                    "batches": 1,
                    "retries": 0,
                }
                for key, value in expected_result.items():
                    self.assertEqual(result[key], value)
                
                self.assertIn("total_execution_time", result)
                self.assertIsInstance(result["total_execution_time"], float)

                mock_gen.assert_called_once_with(num_events)
                mock_pub_sqs.assert_called_once_with(mock_events)

    def test_run_both_mode(self):
        """Test run method in both file and SQS mode."""
        # Arrange
        num_events = 2
        mode = "both"
        output_path = "/tmp/both.jsonl"

        mock_events = [{"id": 1}, {"id": 2}]
        sqs_stats = {"successes": 2, "failures": 0, "batches": 1, "retries": 0}

        with patch.object(self.app, 'generate_events', return_value=mock_events) as mock_gen:
            with patch.object(self.app, 'publish_to_file') as mock_pub_file:
                with patch.object(self.app, 'publish_to_sqs', return_value=sqs_stats) as mock_pub_sqs:
                    # Act
                    result = self.app.run(num_events, mode, output_path)

                    # Assert
                    expected_result = {
                        "file_written": True,
                        "successes": 2,
                        "failures": 0,
                        "batches": 1,
                        "retries": 0,
                    }
                    for key, value in expected_result.items():
                        self.assertEqual(result[key], value)
                    
                    self.assertIn("total_execution_time", result)
                    self.assertIsInstance(result["total_execution_time"], float)

                    mock_gen.assert_called_once_with(num_events)
                    mock_pub_file.assert_called_once_with(mock_events, output_path)
                    mock_pub_sqs.assert_called_once_with(mock_events)

    def test_run_file_mode_with_default_path(self):
        """Test run method in file mode using default output path."""
        # Arrange
        num_events = 1
        mode = "file"

        mock_events = [{"id": 1}]
        with patch.object(self.app, 'generate_events', return_value=mock_events):
            with patch.object(self.app, 'publish_to_file') as mock_pub_file:
                with patch('projects.can_data_platform.src.apps.telemetry_app.time.time', side_effect=[6000.0, 6001.0, 6002.0]):
                    # Act
                    result = self.app.run(num_events, mode)

                    # Assert
                    self.assertTrue(result["file_written"])
                    mock_pub_file.assert_called_once_with(mock_events, self.mock_config.default_output_path)

    def test_run_sqs_mode_without_queue_url(self):
        """Test run method in SQS mode without queue URL configured."""
        # Arrange
        num_events = 1
        mode = "sqs"
        self.mock_config.sqs_queue_url = None

        mock_events = [{"id": 1}]
        with patch.object(self.app, 'generate_events', return_value=mock_events):
            # Act & Assert
            with self.assertRaises(ValueError) as context:
                self.app.run(num_events, mode)

            self.assertIn("SQS_QUEUE_URL is required", str(context.exception))

    def test_run_exception_handling(self):
        """Test run method with exception during execution."""
        # Arrange
        num_events = 1
        mode = "file"

        with patch.object(self.app, 'generate_events', side_effect=Exception("Generation failed")):
            # Act & Assert
            with self.assertRaises(Exception):
                self.app.run(num_events, mode)

            # Verify cleanup is called
            self.mock_publisher.close.assert_called_once()

    def test_run_cleanup_with_attribute_error(self):
        """Test run method cleanup when publisher doesn't have close method."""
        # Arrange
        num_events = 1
        mode = "file"
        self.mock_publisher.close.side_effect = AttributeError("No close method")

        mock_events = [{"id": 1}]
        with patch.object(self.app, 'generate_events', return_value=mock_events):
            with patch.object(self.app, 'publish_to_file'):
                with patch('projects.can_data_platform.src.apps.telemetry_app.time.time', side_effect=[7000.0, 7001.0, 7002.0]):
                    # Act - should not raise exception despite AttributeError in cleanup
                    result = self.app.run(num_events, mode)

                    # Assert
                    self.assertTrue(result["file_written"])

    def test_run_cleanup_with_io_error(self):
        """Test run method cleanup with IO error during close."""
        # Arrange
        num_events = 1
        mode = "file"
        self.mock_publisher.close.side_effect = IOError("Close failed")

        mock_events = [{"id": 1}]
        with patch.object(self.app, 'generate_events', return_value=mock_events):
            with patch.object(self.app, 'publish_to_file'):
                with patch('projects.can_data_platform.src.apps.telemetry_app.time.time', side_effect=[8000.0, 8001.0, 8003.0]):
                    # Act - should not raise exception despite IOError in cleanup
                    result = self.app.run(num_events, mode)

                    # Assert
                    self.assertTrue(result["file_written"])

    def test_publish_to_sqs_zero_successes_rate_calculation(self):
        """Test SQS publishing rate calculation when no events succeeded."""
        # Arrange
        events = [{"id": 1}]

        mock_result = Mock()
        mock_result.successes = 0
        mock_result.failures = 1
        mock_result.batches = 1
        mock_result.retries = 3
        mock_result.success_rate = 0.0
        self.mock_publisher.publish.return_value = mock_result

        with patch('projects.can_data_platform.src.apps.telemetry_app.time.time', side_effect=[9000.0, 9005.0]):
            # Act
            result = self.app.publish_to_sqs(events)

            # Assert - should handle division by zero gracefully
            expected_result = {
                "successes": 0,
                "failures": 1,
                "batches": 1,
                "retries": 3,
            }
            self.assertEqual(result, expected_result)


if __name__ == '__main__':
    unittest.main(verbosity=2)
