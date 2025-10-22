"""Unit tests for latency tracker implementations."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

from projects.can_data_platform.src.metrics.latency_tracker import (
    LatencyTracker,
    LatencyTrackerFactory,
    NoOpLatencyTracker,
)


class TestLatencyTracker(unittest.TestCase):
    """Test LatencyTracker implementation."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.tracker = LatencyTracker(
            flush_every=3,
            output_dir=self.temp_dir,
            sla_threshold_seconds=2.0,
        )

    def test_initialization_default_output_dir(self):
        """Test initialization with default output directory."""
        tracker = LatencyTracker(flush_every=50)
        expected_path = Path("projects/can_data_platform/data/metrics")
        self.assertEqual(tracker.output_dir, expected_path)
        self.assertEqual(tracker.flush_every, 50)
        self.assertEqual(tracker.sla_threshold_seconds, 5.0)

    def test_initialization_custom_parameters(self):
        """Test initialization with custom parameters."""
        with tempfile.TemporaryDirectory() as temp_dir:
            custom_dir = temp_dir
            tracker = LatencyTracker(
                flush_every=200,
                output_dir=custom_dir,
                sla_threshold_seconds=3.5,
            )
            self.assertEqual(tracker.output_dir, Path(custom_dir))
            self.assertEqual(tracker.flush_every, 200)
            self.assertEqual(tracker.sla_threshold_seconds, 3.5)

    def test_record_sqs_latency(self):
        """Test SQS latency recording."""
        start_time = 1000.0
        end_time = 1001.5
        
        self.tracker.record_sqs_latency(start_time, end_time)
        
        self.assertEqual(len(self.tracker.sqs_latencies), 1)
        self.assertEqual(self.tracker.sqs_latencies[0], 1500.0)  # 1.5s = 1500ms

    def test_record_batch_write_latency(self):
        """Test batch write latency recording."""
        start_time = 2000.0
        end_time = 2000.25
        
        self.tracker.record_batch_write_latency(start_time, end_time)
        
        self.assertEqual(len(self.tracker.batch_write_latencies), 1)
        self.assertEqual(self.tracker.batch_write_latencies[0], 250.0)  # 0.25s = 250ms

    def test_record_e2e_latency(self):
        """Test end-to-end latency recording."""
        event_timestamp = 1000.0
        process_timestamp = 1002.5
        
        self.tracker.record_e2e_latency(event_timestamp, process_timestamp)
        
        self.assertEqual(len(self.tracker.e2e_latencies), 1)
        self.assertEqual(self.tracker.e2e_latencies[0], 2.5)  # 2.5 seconds

    def test_record_queue_age_latency_success(self):
        """Test successful queue age latency recording."""
        # SQS SentTimestamp is in milliseconds
        message_sent_timestamp = "1609459200000"  # Jan 1, 2021 00:00:00 UTC
        receive_timestamp = 1609459202.5  # 2.5 seconds later
        
        self.tracker.record_queue_age_latency(message_sent_timestamp, receive_timestamp)
        
        self.assertEqual(len(self.tracker.queue_age_latencies), 1)
        self.assertEqual(self.tracker.queue_age_latencies[0], 2.5)

    def test_record_queue_age_latency_invalid_timestamp(self):
        """Test queue age latency recording with invalid timestamp."""
        invalid_timestamp = "invalid"
        receive_timestamp = 1609459202.5
        
        with patch('projects.can_data_platform.src.metrics.latency_tracker.logger') as mock_logger:
            self.tracker.record_queue_age_latency(invalid_timestamp, receive_timestamp)
            
            mock_logger.warning.assert_called_once()
            self.assertEqual(len(self.tracker.queue_age_latencies), 0)

    def test_step_event(self):
        """Test event stepping increments counters."""
        initial_events_seen = self.tracker.events_seen
        initial_total = self.tracker.total_events_processed
        initial_batch = self.tracker.events_in_current_batch
        
        self.tracker.step_event()
        
        self.assertEqual(self.tracker.events_seen, initial_events_seen + 1)
        self.assertEqual(self.tracker.total_events_processed, initial_total + 1)
        self.assertEqual(self.tracker.events_in_current_batch, initial_batch + 1)

    def test_should_flush_before_threshold(self):
        """Test should_flush returns False before threshold."""
        self.tracker.events_in_current_batch = 2  # Less than flush_every=3
        self.assertFalse(self.tracker.should_flush())

    def test_should_flush_at_threshold(self):
        """Test should_flush returns True at threshold."""
        self.tracker.events_in_current_batch = 3  # Equal to flush_every=3
        self.assertTrue(self.tracker.should_flush())

    def test_should_flush_above_threshold(self):
        """Test should_flush returns True above threshold."""
        self.tracker.events_in_current_batch = 5  # Greater than flush_every=3
        self.assertTrue(self.tracker.should_flush())

    @patch('projects.can_data_platform.src.metrics.latency_tracker.datetime')
    def test_flush_metrics_with_data(self, mock_datetime):
        """Test metrics flushing with data."""
        # Setup mock datetime
        mock_now = MagicMock()
        mock_now.isoformat.return_value = "2024-01-01T12:00:00"
        mock_now.date.return_value = "2024-01-01"
        mock_datetime.now.return_value = mock_now
        
        # Add some test data
        self.tracker.sqs_latencies = [100.0, 200.0, 300.0]
        self.tracker.batch_write_latencies = [50.0, 100.0]
        self.tracker.e2e_latencies = [1.0, 2.0, 3.0]
        self.tracker.queue_age_latencies = [0.5, 1.5]
        self.tracker.events_in_current_batch = 3
        self.tracker.total_events_processed = 10
        self.tracker.events_seen = 15
        
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('projects.can_data_platform.src.metrics.latency_tracker.logger') as mock_logger:
                self.tracker.flush_metrics()
                
                # Verify file was opened and written to
                mock_file.assert_called_once()
                write_calls = mock_file().write.call_args_list
                self.assertGreater(len(write_calls), 0)
                
                # Verify metrics were logged
                mock_logger.info.assert_called_once()
                
                # Verify collections were cleared
                self.assertEqual(len(self.tracker.sqs_latencies), 0)
                self.assertEqual(len(self.tracker.batch_write_latencies), 0)
                self.assertEqual(len(self.tracker.e2e_latencies), 0)
                self.assertEqual(len(self.tracker.queue_age_latencies), 0)
                self.assertEqual(self.tracker.events_in_current_batch, 0)

    def test_flush_metrics_empty_data(self):
        """Test metrics flushing with no data."""
        # Ensure all collections are empty and batch number calculation works
        self.tracker.events_in_current_batch = 0
        self.tracker.events_seen = 0  # This affects batch number calculation
        
        with patch('projects.can_data_platform.src.metrics.latency_tracker.logger') as mock_logger:
            self.tracker.flush_metrics()
            
            # Should log the debug message about skipping empty batch
            mock_logger.debug.assert_any_call("Skipped flushing empty latency batch %d", 0)

    def test_calculate_percentile_empty_list(self):
        """Test percentile calculation with empty list."""
        result = self.tracker._calculate_percentile([], 50)
        self.assertIsNone(result)

    def test_calculate_percentile_single_value(self):
        """Test percentile calculation with single value."""
        result = self.tracker._calculate_percentile([100.5], 95)
        self.assertEqual(result, 100.5)

    def test_calculate_percentile_multiple_values(self):
        """Test percentile calculation with multiple values."""
        values = [10.0, 20.0, 30.0, 40.0, 50.0]
        result = self.tracker._calculate_percentile(values, 50)
        # Should return median (30.0) for 50th percentile
        self.assertEqual(result, 30.0)

    def test_calculate_percentile_error_fallback(self):
        """Test percentile calculation fallback on error."""
        with patch('statistics.quantiles', side_effect=ValueError("Test error")):
            with patch('statistics.median', return_value=25.5) as mock_median:
                values = [10.0, 20.0, 30.0, 40.0]
                result = self.tracker._calculate_percentile(values, 75)
                
                mock_median.assert_called_once_with(values)
                self.assertEqual(result, 25.5)

    @patch('builtins.open', side_effect=OSError("File error"))
    def test_write_metrics_to_file_error(self, mock_open_error):
        """Test metrics file writing with I/O error."""
        metrics = {"test": "data"}
        
        with patch('projects.can_data_platform.src.metrics.latency_tracker.logger') as mock_logger:
            self.tracker._write_metrics_to_file(metrics)
            
            mock_logger.error.assert_called_once()

    def test_check_sla_violations_no_violation(self):
        """Test SLA check with no violations."""
        metrics = {"e2e_p95_s": 1.5}  # Below 2.0s threshold
        
        with patch('projects.can_data_platform.src.metrics.latency_tracker.logger') as mock_logger:
            self.tracker._check_sla_violations(metrics)
            
            # Should not log warning
            mock_logger.warning.assert_not_called()

    def test_check_sla_violations_with_violation(self):
        """Test SLA check with violations."""
        metrics = {"e2e_p95_s": 3.5}  # Above 2.0s threshold
        
        with patch('projects.can_data_platform.src.metrics.latency_tracker.logger') as mock_logger:
            with patch('builtins.print') as mock_print:
                self.tracker._check_sla_violations(metrics)
                
                # Should log warning and print alert
                mock_logger.warning.assert_called_once()
                mock_print.assert_called_once()

    def test_check_sla_violations_missing_metric(self):
        """Test SLA check with missing e2e_p95_s metric."""
        metrics = {"other_metric": 1.0}
        
        with patch('projects.can_data_platform.src.metrics.latency_tracker.logger') as mock_logger:
            self.tracker._check_sla_violations(metrics)
            
            # Should not log warning
            mock_logger.warning.assert_not_called()

    def test_clear_metrics(self):
        """Test metrics clearing."""
        # Add test data
        self.tracker.sqs_latencies = [1.0, 2.0]
        self.tracker.batch_write_latencies = [3.0]
        self.tracker.e2e_latencies = [4.0, 5.0, 6.0]
        self.tracker.queue_age_latencies = [7.0]
        self.tracker.events_in_current_batch = 5
        
        with patch('projects.can_data_platform.src.metrics.latency_tracker.logger') as mock_logger:
            self.tracker._clear_metrics()
            
            # Verify all collections are cleared
            self.assertEqual(len(self.tracker.sqs_latencies), 0)
            self.assertEqual(len(self.tracker.batch_write_latencies), 0)
            self.assertEqual(len(self.tracker.e2e_latencies), 0)
            self.assertEqual(len(self.tracker.queue_age_latencies), 0)
            self.assertEqual(self.tracker.events_in_current_batch, 0)
            
            # Verify logging
            mock_logger.debug.assert_called()

    def test_get_current_stats(self):
        """Test current statistics retrieval."""
        # Setup test state
        self.tracker.events_seen = 25
        self.tracker.total_events_processed = 23
        self.tracker.sqs_latencies = [1.0, 2.0]
        self.tracker.batch_write_latencies = [3.0]
        self.tracker.e2e_latencies = [4.0, 5.0, 6.0]
        
        stats = self.tracker.get_current_stats()
        
        expected_stats = {
            "events_seen": 25,
            "total_events_processed": 23,
            "sqs_latencies_count": 2,
            "batch_write_latencies_count": 1,
            "e2e_latencies_count": 3,
            "next_flush_at": 27,
        }
        
        self.assertEqual(stats, expected_stats)

    def test_flush_with_pending_metrics(self):
        """Test force flush with pending metrics."""
        # Add some data
        self.tracker.sqs_latencies = [100.0]
        
        with patch.object(self.tracker, 'flush_metrics') as mock_flush:
            self.tracker.flush()
            mock_flush.assert_called_once()

    def test_flush_with_no_pending_metrics(self):
        """Test force flush with no pending metrics."""
        # Ensure all collections are empty
        
        with patch.object(self.tracker, 'flush_metrics') as mock_flush:
            self.tracker.flush()
            mock_flush.assert_not_called()


class TestNoOpLatencyTracker(unittest.TestCase):
    """Test NoOpLatencyTracker implementation."""

    def setUp(self):
        """Set up test environment."""
        self.tracker = NoOpLatencyTracker()

    def test_record_sqs_latency_noop(self):
        """Test no-op SQS latency recording."""
        # Should not raise any exceptions
        self.tracker.record_sqs_latency(1000.0, 1001.0)

    def test_record_batch_write_latency_noop(self):
        """Test no-op batch write latency recording."""
        # Should not raise any exceptions
        self.tracker.record_batch_write_latency(2000.0, 2001.0)

    def test_record_e2e_latency_noop(self):
        """Test no-op E2E latency recording."""
        # Should not raise any exceptions
        self.tracker.record_e2e_latency(1000.0, 1005.0)

    def test_record_queue_age_latency_noop(self):
        """Test no-op queue age latency recording."""
        # Should not raise any exceptions
        self.tracker.record_queue_age_latency("1609459200000", 1609459202.5)

    def test_should_flush_always_false(self):
        """Test should_flush always returns False."""
        self.assertFalse(self.tracker.should_flush())

    def test_step_event_noop(self):
        """Test no-op event stepping."""
        # Should not raise any exceptions
        self.tracker.step_event()

    def test_flush_noop(self):
        """Test no-op flush operation."""
        # Should not raise any exceptions
        self.tracker.flush()

    def test_flush_metrics_noop(self):
        """Test no-op metrics flushing."""
        # Should not raise any exceptions
        self.tracker.flush_metrics()


class TestLatencyTrackerFactory(unittest.TestCase):
    """Test LatencyTrackerFactory implementation."""

    def test_create_standard_tracker_default_parameters(self):
        """Test creating standard tracker with default parameters."""
        tracker = LatencyTrackerFactory.create_standard_tracker()
        
        self.assertIsInstance(tracker, LatencyTracker)
        self.assertEqual(tracker.flush_every, 100)
        self.assertEqual(tracker.sla_threshold_seconds, 5.0)
        # Default output dir should be set
        self.assertEqual(
            tracker.output_dir, 
            Path("projects/can_data_platform/data/metrics")
        )

    def test_create_standard_tracker_custom_parameters(self):
        """Test creating standard tracker with custom parameters."""
        with tempfile.TemporaryDirectory() as temp_dir:
            custom_dir = temp_dir
            tracker = LatencyTrackerFactory.create_standard_tracker(
                flush_every=50,
                output_dir=custom_dir,
                sla_threshold_seconds=3.0,
            )
            
            self.assertIsInstance(tracker, LatencyTracker)
            self.assertEqual(tracker.flush_every, 50)
            self.assertEqual(tracker.sla_threshold_seconds, 3.0)
            self.assertEqual(tracker.output_dir, Path(custom_dir))

    def test_create_noop_tracker(self):
        """Test creating no-op tracker."""
        tracker = LatencyTrackerFactory.create_noop_tracker()
        
        self.assertIsInstance(tracker, NoOpLatencyTracker)


if __name__ == "__main__":
    unittest.main()