"""Unit tests for progress tracking functionality."""

import unittest
from unittest.mock import MagicMock, patch

import pytest

from projects.can_data_platform.src.tracking.progress import (
    NoOpProgressTracker,
    ProgressTracker,
    ProgressTrackerFactory,
    TqdmProgressTracker,
)


class TestProgressTrackerInterface(unittest.TestCase):
    """Test ProgressTracker abstract base class."""

    def test_interface_cannot_be_instantiated(self):
        """Test that the interface cannot be instantiated directly."""
        with pytest.raises(TypeError):
            ProgressTracker()

    def test_interface_requires_implementation(self):
        """Test that concrete classes must implement required methods."""
        class IncompleteTracker(ProgressTracker):
            pass

        with pytest.raises(TypeError):
            IncompleteTracker()


class TestTqdmProgressTracker(unittest.TestCase):
    """Test TqdmProgressTracker implementation."""

    def setUp(self):
        """Set up test instances."""
        self.tracker = TqdmProgressTracker()
        self.custom_tracker = TqdmProgressTracker(unit="events")

    def test_initialization_default_unit(self):
        """Test tracker initialization with default unit."""
        tracker = TqdmProgressTracker()
        
        assert tracker.unit == "items"
        assert tracker._progress_bar is None

    def test_initialization_custom_unit(self):
        """Test tracker initialization with custom unit."""
        tracker = TqdmProgressTracker(unit="messages")
        
        assert tracker.unit == "messages"
        assert tracker._progress_bar is None

    @patch('projects.can_data_platform.src.tracking.progress.tqdm')
    def test_start_creates_progress_bar(self, mock_tqdm):
        """Test that start() creates a tqdm progress bar."""
        mock_bar = MagicMock()
        mock_tqdm.return_value = mock_bar
        
        self.tracker.start(total=100, description="Processing")
        
        mock_tqdm.assert_called_once()
        call_kwargs = mock_tqdm.call_args[1]
        assert call_kwargs['total'] == 100
        assert call_kwargs['desc'] == "Processing"
        assert call_kwargs['unit'] == "items"
        assert 'bar_format' in call_kwargs
        assert self.tracker._progress_bar == mock_bar

    @patch('projects.can_data_platform.src.tracking.progress.tqdm')
    def test_start_with_custom_unit(self, mock_tqdm):
        """Test start() with custom unit."""
        mock_bar = MagicMock()
        mock_tqdm.return_value = mock_bar
        
        custom_tracker = TqdmProgressTracker(unit="events")
        custom_tracker.start(total=50, description="Loading")
        
        call_kwargs = mock_tqdm.call_args[1]
        assert call_kwargs['unit'] == "events"

    @patch('projects.can_data_platform.src.tracking.progress.tqdm')
    def test_update_with_progress_bar(self, mock_tqdm):
        """Test update() when progress bar exists."""
        mock_bar = MagicMock()
        mock_tqdm.return_value = mock_bar
        
        self.tracker.start(total=100, description="Processing")
        self.tracker.update(5)
        
        mock_bar.update.assert_called_once_with(5)

    @patch('projects.can_data_platform.src.tracking.progress.tqdm')
    def test_update_default_increment(self, mock_tqdm):
        """Test update() with default increment of 1."""
        mock_bar = MagicMock()
        mock_tqdm.return_value = mock_bar
        
        self.tracker.start(total=100, description="Processing")
        self.tracker.update()
        
        mock_bar.update.assert_called_once_with(1)

    def test_update_without_progress_bar(self):
        """Test update() when progress bar doesn't exist."""
        # Should not raise an error
        self.tracker.update(5)
        self.tracker.update()

    @patch('projects.can_data_platform.src.tracking.progress.tqdm')
    def test_set_postfix_with_progress_bar(self, mock_tqdm):
        """Test set_postfix() when progress bar exists."""
        mock_bar = MagicMock()
        mock_tqdm.return_value = mock_bar
        
        self.tracker.start(total=100, description="Processing")
        postfix_data = {"success": 10, "failed": 2}
        self.tracker.set_postfix(postfix_data)
        
        mock_bar.set_postfix.assert_called_once_with(postfix_data)

    def test_set_postfix_without_progress_bar(self):
        """Test set_postfix() when progress bar doesn't exist."""
        # Should not raise an error
        self.tracker.set_postfix({"test": "value"})

    @patch('projects.can_data_platform.src.tracking.progress.tqdm')
    def test_write_with_progress_bar(self, mock_tqdm):
        """Test write() when progress bar exists."""
        mock_bar = MagicMock()
        mock_tqdm.return_value = mock_bar
        
        self.tracker.start(total=100, description="Processing")
        message = "Test message"
        self.tracker.write(message)
        
        mock_bar.write.assert_called_once_with(message)

    def test_write_without_progress_bar(self):
        """Test write() when progress bar doesn't exist."""
        # Should not raise an error
        self.tracker.write("Test message")

    @patch('projects.can_data_platform.src.tracking.progress.tqdm')
    def test_close_with_progress_bar(self, mock_tqdm):
        """Test close() when progress bar exists."""
        mock_bar = MagicMock()
        mock_tqdm.return_value = mock_bar
        
        self.tracker.start(total=100, description="Processing")
        self.tracker.close()
        
        mock_bar.close.assert_called_once()
        assert self.tracker._progress_bar is None

    def test_close_without_progress_bar(self):
        """Test close() when progress bar doesn't exist."""
        # Should not raise an error
        self.tracker.close()
        assert self.tracker._progress_bar is None

    @patch('projects.can_data_platform.src.tracking.progress.tqdm')
    def test_full_lifecycle(self, mock_tqdm):
        """Test full lifecycle: start, update, set_postfix, write, close."""
        mock_bar = MagicMock()
        mock_tqdm.return_value = mock_bar
        
        # Start
        self.tracker.start(total=100, description="Processing")
        assert self.tracker._progress_bar == mock_bar
        
        # Update multiple times
        self.tracker.update(10)
        self.tracker.update(5)
        self.tracker.update()
        
        # Set postfix
        self.tracker.set_postfix({"rate": "10/s"})
        
        # Write message
        self.tracker.write("Checkpoint reached")
        
        # Close
        self.tracker.close()
        
        # Verify all calls
        assert mock_bar.update.call_count == 3
        mock_bar.set_postfix.assert_called_once()
        mock_bar.write.assert_called_once()
        mock_bar.close.assert_called_once()
        assert self.tracker._progress_bar is None

    def test_interface_compliance(self):
        """Test that TqdmProgressTracker implements the interface correctly."""
        assert isinstance(self.tracker, ProgressTracker)
        
        # Should have all required methods
        assert hasattr(self.tracker, 'start')
        assert hasattr(self.tracker, 'update')
        assert hasattr(self.tracker, 'set_postfix')
        assert hasattr(self.tracker, 'write')
        assert hasattr(self.tracker, 'close')


class TestNoOpProgressTracker(unittest.TestCase):
    """Test NoOpProgressTracker implementation."""

    def setUp(self):
        """Set up test instance."""
        self.tracker = NoOpProgressTracker()

    def test_start_no_operation(self):
        """Test that start() performs no operation."""
        # Should not raise any error
        self.tracker.start(total=100, description="Processing")
        self.tracker.start(total=0, description="")

    def test_update_no_operation(self):
        """Test that update() performs no operation."""
        # Should not raise any error
        self.tracker.update(10)
        self.tracker.update()
        self.tracker.update(0)

    def test_set_postfix_no_operation(self):
        """Test that set_postfix() performs no operation."""
        # Should not raise any error
        self.tracker.set_postfix({"test": "value"})
        self.tracker.set_postfix({})

    def test_write_no_operation(self):
        """Test that write() performs no operation."""
        # Should not raise any error
        self.tracker.write("Test message")
        self.tracker.write("")

    def test_close_no_operation(self):
        """Test that close() performs no operation."""
        # Should not raise any error
        self.tracker.close()

    def test_full_lifecycle_no_operation(self):
        """Test full lifecycle with no operations."""
        # None of these should raise errors
        self.tracker.start(total=100, description="Processing")
        self.tracker.update(10)
        self.tracker.update(5)
        self.tracker.set_postfix({"rate": "10/s"})
        self.tracker.write("Message")
        self.tracker.close()

    def test_interface_compliance(self):
        """Test that NoOpProgressTracker implements the interface correctly."""
        assert isinstance(self.tracker, ProgressTracker)
        
        # Should have all required methods
        assert hasattr(self.tracker, 'start')
        assert hasattr(self.tracker, 'update')
        assert hasattr(self.tracker, 'set_postfix')
        assert hasattr(self.tracker, 'write')
        assert hasattr(self.tracker, 'close')

    def test_multiple_operations_safe(self):
        """Test that multiple operations are safe."""
        # Test that we can call operations multiple times without issues
        for _ in range(10):
            self.tracker.start(total=100, description="Test")
            self.tracker.update(1)
            self.tracker.set_postfix({"test": "value"})
            self.tracker.write("message")
            self.tracker.close()


class TestProgressTrackerFactory(unittest.TestCase):
    """Test ProgressTrackerFactory functionality."""

    def test_create_tqdm_tracker_default(self):
        """Test creating tqdm tracker with default parameters."""
        tracker = ProgressTrackerFactory.create_tqdm_tracker()
        
        assert isinstance(tracker, TqdmProgressTracker)
        assert tracker.unit == "items"
        assert tracker._progress_bar is None

    def test_create_tqdm_tracker_custom_unit(self):
        """Test creating tqdm tracker with custom unit."""
        tracker = ProgressTrackerFactory.create_tqdm_tracker(unit="messages")
        
        assert isinstance(tracker, TqdmProgressTracker)
        assert tracker.unit == "messages"

    def test_create_noop_tracker(self):
        """Test creating no-op tracker."""
        tracker = ProgressTrackerFactory.create_noop_tracker()
        
        assert isinstance(tracker, NoOpProgressTracker)

    def test_factory_creates_independent_instances(self):
        """Test that factory creates independent tracker instances."""
        tracker1 = ProgressTrackerFactory.create_tqdm_tracker()
        tracker2 = ProgressTrackerFactory.create_tqdm_tracker()
        
        assert tracker1 is not tracker2

    def test_noop_tracker_instances_are_independent(self):
        """Test that no-op tracker instances are independent."""
        tracker1 = ProgressTrackerFactory.create_noop_tracker()
        tracker2 = ProgressTrackerFactory.create_noop_tracker()
        
        assert tracker1 is not tracker2


class TestIntegrationScenarios(unittest.TestCase):
    """Test integration scenarios and edge cases."""

    @patch('projects.can_data_platform.src.tracking.progress.tqdm')
    def test_multiple_progress_cycles(self, mock_tqdm):
        """Test multiple progress tracking cycles."""
        mock_bar1 = MagicMock()
        mock_bar2 = MagicMock()
        mock_tqdm.side_effect = [mock_bar1, mock_bar2]
        
        tracker = TqdmProgressTracker()
        
        # First cycle
        tracker.start(total=50, description="First")
        tracker.update(10)
        tracker.close()
        
        # Second cycle
        tracker.start(total=100, description="Second")
        tracker.update(20)
        tracker.close()
        
        # Verify both cycles completed
        mock_bar1.close.assert_called_once()
        mock_bar2.close.assert_called_once()

    def test_noop_tracker_with_extreme_values(self):
        """Test no-op tracker with extreme values."""
        tracker = NoOpProgressTracker()
        
        # Should handle extreme values without issues
        tracker.start(total=999999999, description="Large")
        tracker.update(999999999)
        tracker.set_postfix({"key" * 100: "value" * 100})
        tracker.write("message" * 1000)
        tracker.close()

    @patch('projects.can_data_platform.src.tracking.progress.tqdm')
    def test_bar_format_customization(self, mock_tqdm):
        """Test that bar format is properly customized."""
        mock_bar = MagicMock()
        mock_tqdm.return_value = mock_bar
        
        tracker = TqdmProgressTracker()
        tracker.start(total=100, description="Test")
        
        # Verify bar_format is set
        call_kwargs = mock_tqdm.call_args[1]
        assert 'bar_format' in call_kwargs
        bar_format = call_kwargs['bar_format']
        assert 'l_bar' in bar_format
        assert 'bar' in bar_format
        assert 'n_fmt' in bar_format
        assert 'total_fmt' in bar_format
