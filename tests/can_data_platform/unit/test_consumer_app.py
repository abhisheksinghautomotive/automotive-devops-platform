"""Comprehensive unit tests for ConsumerApp module."""

import logging
import signal
import sys
import time
import unittest
from unittest.mock import Mock, patch, MagicMock, call

from projects.can_data_platform.src.apps.consumer_app import ConsumerApp
from projects.can_data_platform.src.config.consumer_config import ConsumerConfig


class TestConsumerApp(unittest.TestCase):
    """Test suite for ConsumerApp class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.mock_config = Mock(spec=ConsumerConfig)
        self.mock_config.queue_url = "https://sqs.us-east-1.amazonaws.com/123456789/test-queue"
        self.mock_config.aws_region = "us-east-1"
        self.mock_config.batch_size = 10
        self.mock_config.poll_interval = 1
        self.mock_config.max_retries = 3
        self.mock_config.max_wait_time = 20
        self.mock_config.log_level = "INFO"
        self.mock_config.log_file = None
        self.mock_config.latency_output_dir = None
        self.mock_config.latency_flush_every = 100
        self.mock_config.sla_threshold_seconds = 5.0

    @patch('projects.can_data_platform.src.apps.consumer_app.SQSConsumerFactory')
    @patch('projects.can_data_platform.src.apps.consumer_app.MessageProcessorFactory')
    @patch('projects.can_data_platform.src.apps.consumer_app.LatencyTrackerFactory')
    @patch('projects.can_data_platform.src.apps.consumer_app.signal.signal')
    def test_consumer_app_initialization(self, mock_signal, mock_latency_factory, 
                                       mock_processor_factory, mock_consumer_factory):
        """Test ConsumerApp proper initialization."""
        # Arrange
        mock_latency_tracker = Mock()
        mock_processor = Mock()
        mock_consumer = Mock()
        
        mock_latency_factory.create_tracker.return_value = mock_latency_tracker
        mock_processor_factory.create_processor.return_value = mock_processor
        mock_consumer_factory.create_consumer.return_value = mock_consumer

        # Act
        app = ConsumerApp(self.mock_config)

        # Assert
        self.assertEqual(app.config, self.mock_config)
        self.assertFalse(app._running)
        self.assertEqual(app.total_stats["messages_consumed"], 0)
        self.assertEqual(app.total_stats["messages_processed"], 0)
        self.assertEqual(app.consecutive_empty_batches, 0)
        self.assertEqual(app.max_empty_before_suggestion, 3)
        
        # Verify factory calls
        mock_latency_factory.create_tracker.assert_called_once_with(
            enabled=False,  # latency_output_dir is None
            output_dir=None,
            flush_every=100,
            sla_threshold_seconds=5.0
        )
        
        mock_processor_factory.create_processor.assert_called_once_with(
            processor_type="telemetry"
        )
        
        mock_consumer_factory.create_consumer.assert_called_once()
        
        # Verify signal handlers were set up
        self.assertEqual(mock_signal.call_count, 2)

    @patch('projects.can_data_platform.src.apps.consumer_app.SQSConsumerFactory')
    @patch('projects.can_data_platform.src.apps.consumer_app.MessageProcessorFactory')
    @patch('projects.can_data_platform.src.apps.consumer_app.LatencyTrackerFactory')
    @patch('projects.can_data_platform.src.apps.consumer_app.signal.signal')
    def test_consumer_app_with_latency_tracking(self, mock_signal, mock_latency_factory,
                                              mock_processor_factory, mock_consumer_factory):
        """Test ConsumerApp initialization with latency tracking enabled."""
        # Arrange
        self.mock_config.latency_output_dir = "/tmp/latency"
        
        mock_latency_tracker = Mock()
        mock_processor = Mock()
        mock_consumer = Mock()
        
        mock_latency_factory.create_tracker.return_value = mock_latency_tracker
        mock_processor_factory.create_processor.return_value = mock_processor
        mock_consumer_factory.create_consumer.return_value = mock_consumer

        # Act
        app = ConsumerApp(self.mock_config)

        # Assert
        mock_latency_factory.create_tracker.assert_called_once_with(
            enabled=True,  # latency_output_dir is set
            output_dir="/tmp/latency",
            flush_every=100,
            sla_threshold_seconds=5.0
        )

    @patch('projects.can_data_platform.src.apps.consumer_app.SQSConsumerFactory')
    @patch('projects.can_data_platform.src.apps.consumer_app.MessageProcessorFactory')
    @patch('projects.can_data_platform.src.apps.consumer_app.LatencyTrackerFactory')
    @patch('projects.can_data_platform.src.apps.consumer_app.signal.signal')
    def test_setup_logging_console_only(self, mock_signal, mock_latency_factory,
                                       mock_processor_factory, mock_consumer_factory):
        """Test logging setup with console handler only."""
        # Arrange
        mock_latency_factory.create_tracker.return_value = Mock()
        mock_processor_factory.create_processor.return_value = Mock()
        mock_consumer_factory.create_consumer.return_value = Mock()

        # Act
        app = ConsumerApp(self.mock_config)

        # Assert
        self.assertIsInstance(app.logger, logging.Logger)
        self.assertEqual(app.logger.name, "consumer_app")
        self.assertEqual(app.logger.level, logging.INFO)

    @patch('projects.can_data_platform.src.apps.consumer_app.SQSConsumerFactory')
    @patch('projects.can_data_platform.src.apps.consumer_app.MessageProcessorFactory')
    @patch('projects.can_data_platform.src.apps.consumer_app.LatencyTrackerFactory')
    @patch('projects.can_data_platform.src.apps.consumer_app.signal.signal')
    def test_setup_logging_with_file(self, mock_signal, mock_latency_factory,
                                    mock_processor_factory, mock_consumer_factory):
        """Test logging setup with file handler."""
        # Arrange
        self.mock_config.log_file = "/tmp/test.log"
        
        mock_latency_factory.create_tracker.return_value = Mock()
        mock_processor_factory.create_processor.return_value = Mock()
        mock_consumer_factory.create_consumer.return_value = Mock()

        # Act
        with patch('logging.FileHandler') as mock_file_handler:
            app = ConsumerApp(self.mock_config)
            
            # Assert
            mock_file_handler.assert_called_once_with("/tmp/test.log")

    @patch('projects.can_data_platform.src.apps.consumer_app.SQSConsumerFactory')
    @patch('projects.can_data_platform.src.apps.consumer_app.MessageProcessorFactory')
    @patch('projects.can_data_platform.src.apps.consumer_app.LatencyTrackerFactory')
    @patch('projects.can_data_platform.src.apps.consumer_app.signal.signal')
    def test_signal_handler(self, mock_signal, mock_latency_factory,
                           mock_processor_factory, mock_consumer_factory):
        """Test signal handler for graceful shutdown."""
        # Arrange
        mock_latency_factory.create_tracker.return_value = Mock()
        mock_processor_factory.create_processor.return_value = Mock()
        mock_consumer_factory.create_consumer.return_value = Mock()

        app = ConsumerApp(self.mock_config)
        app._running = True

        # Act
        app._signal_handler(signal.SIGTERM, None)

        # Assert
        self.assertFalse(app._running)

    @patch('projects.can_data_platform.src.apps.consumer_app.SQSConsumerFactory')
    @patch('projects.can_data_platform.src.apps.consumer_app.MessageProcessorFactory')
    @patch('projects.can_data_platform.src.apps.consumer_app.LatencyTrackerFactory')
    @patch('projects.can_data_platform.src.apps.consumer_app.signal.signal')
    def test_initialize_consumer(self, mock_signal, mock_latency_factory,
                                mock_processor_factory, mock_consumer_factory):
        """Test consumer initialization with configuration logging."""
        # Arrange
        mock_latency_factory.create_tracker.return_value = Mock()
        mock_processor_factory.create_processor.return_value = Mock()
        mock_consumer_factory.create_consumer.return_value = Mock()

        app = ConsumerApp(self.mock_config)

        # Act
        with patch.object(app.logger, 'info') as mock_log_info:
            app._initialize_consumer()

            # Assert
            mock_log_info.assert_any_call("Starting SQS batch consumer application...")
            mock_log_info.assert_any_call("Queue URL: %s", self.mock_config.queue_url)
            mock_log_info.assert_any_call("Batch size: %s", self.mock_config.batch_size)
            mock_log_info.assert_any_call("Poll interval: %s seconds", self.mock_config.poll_interval)
            mock_log_info.assert_any_call("Max retries: %s", self.mock_config.max_retries)
            mock_log_info.assert_any_call("Latency tracking disabled")

    @patch('projects.can_data_platform.src.apps.consumer_app.SQSConsumerFactory')
    @patch('projects.can_data_platform.src.apps.consumer_app.MessageProcessorFactory')
    @patch('projects.can_data_platform.src.apps.consumer_app.LatencyTrackerFactory')
    @patch('projects.can_data_platform.src.apps.consumer_app.signal.signal')
    def test_initialize_consumer_with_latency(self, mock_signal, mock_latency_factory,
                                             mock_processor_factory, mock_consumer_factory):
        """Test consumer initialization with latency tracking enabled."""
        # Arrange
        self.mock_config.latency_output_dir = "/tmp/latency"
        
        mock_latency_factory.create_tracker.return_value = Mock()
        mock_processor_factory.create_processor.return_value = Mock()
        mock_consumer_factory.create_consumer.return_value = Mock()

        app = ConsumerApp(self.mock_config)

        # Act
        with patch.object(app.logger, 'info') as mock_log_info:
            app._initialize_consumer()

            # Assert
            mock_log_info.assert_any_call(
                "Latency tracking enabled, output: %s", "/tmp/latency"
            )

    @patch('projects.can_data_platform.src.apps.consumer_app.SQSConsumerFactory')
    @patch('projects.can_data_platform.src.apps.consumer_app.MessageProcessorFactory')
    @patch('projects.can_data_platform.src.apps.consumer_app.LatencyTrackerFactory')
    @patch('projects.can_data_platform.src.apps.consumer_app.signal.signal')
    @patch('projects.can_data_platform.src.apps.consumer_app.time.sleep')
    def test_main_processing_loop_no_messages(self, mock_sleep, mock_signal, mock_latency_factory,
                                             mock_processor_factory, mock_consumer_factory):
        """Test main processing loop when no messages are available."""
        # Arrange
        mock_latency_factory.create_tracker.return_value = Mock()
        mock_processor_factory.create_processor.return_value = Mock()
        mock_consumer_factory.create_consumer.return_value = Mock()

        app = ConsumerApp(self.mock_config)

        # Mock the _process_batch method to return empty result
        mock_result = Mock()
        mock_result.messages_processed = 0

        # Simulate stopping after sleep is called
        app._running = True
        iterations = 0

        def stop_after_sleep(*args, **kwargs):
            nonlocal iterations
            iterations += 1
            if iterations >= 2:  # After first iteration and sleep
                app._running = False
            return mock_result

        def mock_sleep_side_effect(*args, **kwargs):
            # Stop running after sleep is called
            app._running = False

        mock_sleep.side_effect = mock_sleep_side_effect

        # Act
        with patch.object(app, '_process_batch', side_effect=stop_after_sleep):
            app._main_processing_loop()

        # Assert
        mock_sleep.assert_called_once_with(self.mock_config.poll_interval)

    @patch('projects.can_data_platform.src.apps.consumer_app.SQSConsumerFactory')
    @patch('projects.can_data_platform.src.apps.consumer_app.MessageProcessorFactory')
    @patch('projects.can_data_platform.src.apps.consumer_app.LatencyTrackerFactory')
    @patch('projects.can_data_platform.src.apps.consumer_app.signal.signal')
    def test_run_method_complete_workflow(self, mock_signal, mock_latency_factory,
                                          mock_processor_factory, mock_consumer_factory):
        """Test complete run method workflow."""
        # Arrange
        mock_latency_factory.create_tracker.return_value = Mock()
        mock_processor_factory.create_processor.return_value = Mock()
        mock_consumer_factory.create_consumer.return_value = Mock()

        app = ConsumerApp(self.mock_config)

        # Mock all the internal methods
        with patch.object(app, '_initialize_consumer') as mock_init, \
             patch.object(app, '_main_processing_loop') as mock_loop, \
             patch.object(app, '_shutdown') as mock_shutdown:
            
            # Act
            app.run()

            # Assert
            mock_init.assert_called_once()
            mock_loop.assert_called_once()
            mock_shutdown.assert_called_once()
            self.assertTrue(app._running)

    @patch('projects.can_data_platform.src.apps.consumer_app.SQSConsumerFactory')
    @patch('projects.can_data_platform.src.apps.consumer_app.MessageProcessorFactory')
    @patch('projects.can_data_platform.src.apps.consumer_app.LatencyTrackerFactory')
    @patch('projects.can_data_platform.src.apps.consumer_app.signal.signal')
    def test_run_method_keyboard_interrupt(self, mock_signal, mock_latency_factory,
                                          mock_processor_factory, mock_consumer_factory):
        """Test run method handling KeyboardInterrupt."""
        # Arrange
        mock_latency_factory.create_tracker.return_value = Mock()
        mock_processor_factory.create_processor.return_value = Mock()
        mock_consumer_factory.create_consumer.return_value = Mock()

        app = ConsumerApp(self.mock_config)

        # Mock internal methods
        with patch.object(app, '_initialize_consumer'), \
             patch.object(app, '_main_processing_loop', side_effect=KeyboardInterrupt), \
             patch.object(app, '_shutdown') as mock_shutdown, \
             patch.object(app.logger, 'info') as mock_log_info:
            
            # Act
            app.run()

            # Assert
            mock_shutdown.assert_called_once()
            mock_log_info.assert_any_call("Received keyboard interrupt")

    @patch('projects.can_data_platform.src.apps.consumer_app.SQSConsumerFactory')
    @patch('projects.can_data_platform.src.apps.consumer_app.MessageProcessorFactory')
    @patch('projects.can_data_platform.src.apps.consumer_app.LatencyTrackerFactory')
    @patch('projects.can_data_platform.src.apps.consumer_app.signal.signal')
    def test_run_method_critical_error(self, mock_signal, mock_latency_factory,
                                      mock_processor_factory, mock_consumer_factory):
        """Test run method handling critical errors."""
        # Arrange
        mock_latency_factory.create_tracker.return_value = Mock()
        mock_processor_factory.create_processor.return_value = Mock()
        mock_consumer_factory.create_consumer.return_value = Mock()

        app = ConsumerApp(self.mock_config)
        test_error = Exception("Critical test error")

        # Mock internal methods
        with patch.object(app, '_initialize_consumer'), \
             patch.object(app, '_main_processing_loop', side_effect=test_error), \
             patch.object(app, '_shutdown') as mock_shutdown, \
             patch.object(app.logger, 'error') as mock_log_error:
            
            # Act & Assert
            with self.assertRaises(Exception) as context:
                app.run()
            
            self.assertEqual(str(context.exception), "Critical test error")
            mock_shutdown.assert_called_once()
            mock_log_error.assert_called_once_with(
                "Critical error in consumer application: %s", test_error
            )


class TestConsumerAppProcessBatch(unittest.TestCase):
    """Test suite for ConsumerApp _process_batch method."""

    def setUp(self):
        """Set up test fixtures for batch processing tests."""
        self.mock_config = Mock(spec=ConsumerConfig)
        self.mock_config.queue_url = "https://sqs.us-east-1.amazonaws.com/123456789/test-queue"
        self.mock_config.aws_region = "us-east-1"
        self.mock_config.batch_size = 10
        self.mock_config.poll_interval = 1
        self.mock_config.max_retries = 3
        self.mock_config.max_wait_time = 20
        self.mock_config.log_level = "INFO"
        self.mock_config.log_file = None
        self.mock_config.latency_output_dir = None
        self.mock_config.latency_flush_every = 100
        self.mock_config.sla_threshold_seconds = 5.0

    @patch('projects.can_data_platform.src.apps.consumer_app.SQSConsumerFactory')
    @patch('projects.can_data_platform.src.apps.consumer_app.MessageProcessorFactory')
    @patch('projects.can_data_platform.src.apps.consumer_app.LatencyTrackerFactory')
    @patch('projects.can_data_platform.src.apps.consumer_app.signal.signal')
    def test_process_batch_success(self, mock_signal, mock_latency_factory,
                                  mock_processor_factory, mock_consumer_factory):
        """Test successful batch processing."""
        # Arrange
        mock_latency_factory.create_tracker.return_value = Mock()
        mock_processor_factory.create_processor.return_value = Mock()
        mock_consumer = Mock()
        mock_consumer_factory.create_consumer.return_value = mock_consumer

        # Mock batch result with correct attribute names
        mock_result = Mock()
        mock_result.consumed = 5  # This is what the code actually uses
        mock_result.messages_processed = 5
        mock_result.messages_deleted = 5
        mock_result.errors = 0
        mock_result.deletion_errors = 0
        mock_consumer.consume_batch.return_value = mock_result

        app = ConsumerApp(self.mock_config)

        # Act
        result = app._process_batch()

        # Assert
        self.assertEqual(result, mock_result)
        self.assertEqual(app.total_stats["messages_consumed"], 5)
        self.assertEqual(app.total_stats["messages_processed"], 5)
        self.assertEqual(app.total_stats["messages_deleted"], 5)
        self.assertEqual(app.total_stats["batches_processed"], 1)
        self.assertEqual(app.consecutive_empty_batches, 0)

    @patch('projects.can_data_platform.src.apps.consumer_app.SQSConsumerFactory')
    @patch('projects.can_data_platform.src.apps.consumer_app.MessageProcessorFactory')
    @patch('projects.can_data_platform.src.apps.consumer_app.LatencyTrackerFactory')
    @patch('projects.can_data_platform.src.apps.consumer_app.signal.signal')
    def test_process_batch_empty_queue(self, mock_signal, mock_latency_factory,
                                      mock_processor_factory, mock_consumer_factory):
        """Test batch processing with empty queue."""
        # Arrange
        mock_latency_factory.create_tracker.return_value = Mock()
        mock_processor_factory.create_processor.return_value = Mock()
        mock_consumer = Mock()
        mock_consumer_factory.create_consumer.return_value = mock_consumer

        # Mock empty batch result with correct attribute names
        mock_result = Mock()
        mock_result.consumed = 0  # This is what the code actually uses
        mock_result.messages_processed = 0
        mock_result.messages_deleted = 0
        mock_result.errors = 0
        mock_result.deletion_errors = 0
        mock_consumer.consume_batch.return_value = mock_result

        app = ConsumerApp(self.mock_config)

        # Act
        app._process_batch()  # Don't need to capture result

        # Assert
        self.assertEqual(app.consecutive_empty_batches, 1)
        self.assertEqual(app.total_stats["batches_processed"], 1)


class TestConsumerAppArguments(unittest.TestCase):
    """Test suite for ConsumerApp argument parsing."""

    def test_create_argument_parser(self):
        """Test argument parser creation."""
        from projects.can_data_platform.src.apps.consumer_app import create_argument_parser
        
        parser = create_argument_parser()
        
        # Test parsing arguments
        args = parser.parse_args(['--batch-size', '5', '--log-level', 'DEBUG'])
        self.assertEqual(args.batch_size, 5)
        self.assertEqual(args.log_level, 'DEBUG')


class TestConsumerAppMainFunction(unittest.TestCase):
    """Test suite for main function."""

    @patch('projects.can_data_platform.src.apps.consumer_app.ConsumerConfigManager')
    @patch('projects.can_data_platform.src.apps.consumer_app.ConsumerApp')
    @patch('projects.can_data_platform.src.apps.consumer_app.create_argument_parser')
    def test_main_success(self, mock_parser, mock_app_class, mock_config_manager):
        """Test main function successful execution."""
        from projects.can_data_platform.src.apps.consumer_app import main
        
        # Arrange
        mock_args = Mock()
        mock_parser_instance = Mock()
        mock_parser_instance.parse_args.return_value = mock_args
        mock_parser.return_value = mock_parser_instance
        
        mock_config = Mock()
        mock_config_manager.create_from_args.return_value = mock_config
        
        mock_app = Mock()
        mock_app_class.return_value = mock_app
        
        # Act
        main()
        
        # Assert
        mock_config_manager.create_from_args.assert_called_once_with(mock_args)
        mock_app_class.assert_called_once_with(mock_config)
        mock_app.run.assert_called_once()

    @patch('projects.can_data_platform.src.apps.consumer_app.ConsumerConfigManager')
    @patch('projects.can_data_platform.src.apps.consumer_app.create_argument_parser')
    @patch('builtins.print')
    def test_main_with_value_error(self, mock_print, mock_parser, mock_config_manager):
        """Test main function handles ValueError."""
        from projects.can_data_platform.src.apps.consumer_app import main
        
        # Arrange
        mock_args = Mock()
        mock_parser_instance = Mock()
        mock_parser_instance.parse_args.return_value = mock_args
        mock_parser.return_value = mock_parser_instance
        
        mock_config_manager.create_from_args.side_effect = ValueError("Invalid config")
        
        # Act
        main()
        
        # Assert
        mock_print.assert_called_once()
        call_args = mock_print.call_args[0][0]
        self.assertIn("Failed to start consumer application", call_args)

    @patch('projects.can_data_platform.src.apps.consumer_app.ConsumerConfigManager')
    @patch('projects.can_data_platform.src.apps.consumer_app.create_argument_parser')
    @patch('builtins.print')
    def test_main_with_file_not_found_error(self, mock_print, mock_parser, mock_config_manager):
        """Test main function handles FileNotFoundError."""
        from projects.can_data_platform.src.apps.consumer_app import main
        
        # Arrange
        mock_args = Mock()
        mock_parser_instance = Mock()
        mock_parser_instance.parse_args.return_value = mock_args
        mock_parser.return_value = mock_parser_instance
        
        mock_config_manager.create_from_args.side_effect = FileNotFoundError("Config not found")
        
        # Act
        main()
        
        # Assert
        mock_print.assert_called_once()

    @patch('projects.can_data_platform.src.apps.consumer_app.ConsumerConfigManager')
    @patch('projects.can_data_platform.src.apps.consumer_app.create_argument_parser')
    @patch('builtins.print')
    def test_main_with_connection_error(self, mock_print, mock_parser, mock_config_manager):
        """Test main function handles ConnectionError."""
        from projects.can_data_platform.src.apps.consumer_app import main
        
        # Arrange
        mock_args = Mock()
        mock_parser_instance = Mock()
        mock_parser_instance.parse_args.return_value = mock_args
        mock_parser.return_value = mock_parser_instance
        
        mock_config_manager.create_from_args.side_effect = ConnectionError("Cannot connect")
        
        # Act
        main()
        
        # Assert
        mock_print.assert_called_once()


class TestConsumerAppErrorHandling(unittest.TestCase):
    """Test suite for error handling in ConsumerApp."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_config = Mock(spec=ConsumerConfig)
        self.mock_config.queue_url = "https://sqs.us-east-1.amazonaws.com/123456789/test-queue"
        self.mock_config.aws_region = "us-east-1"
        self.mock_config.batch_size = 10
        self.mock_config.poll_interval = 1
        self.mock_config.max_retries = 3
        self.mock_config.max_wait_time = 20
        self.mock_config.log_level = "INFO"
        self.mock_config.log_file = None
        self.mock_config.latency_output_dir = None
        self.mock_config.latency_flush_every = 100
        self.mock_config.sla_threshold_seconds = 5.0

    @patch('projects.can_data_platform.src.apps.consumer_app.SQSConsumerFactory')
    @patch('projects.can_data_platform.src.apps.consumer_app.MessageProcessorFactory')
    @patch('projects.can_data_platform.src.apps.consumer_app.LatencyTrackerFactory')
    @patch('projects.can_data_platform.src.apps.consumer_app.signal.signal')
    @patch('projects.can_data_platform.src.apps.consumer_app.time.sleep')
    def test_main_processing_loop_timeout_error(self, mock_sleep, mock_signal,
                                                mock_latency_factory, mock_processor_factory,
                                                mock_consumer_factory):
        """Test main processing loop handles TimeoutError."""
        # Arrange
        mock_latency_factory.create_tracker.return_value = Mock()
        mock_processor_factory.create_processor.return_value = Mock()
        mock_consumer_factory.create_consumer.return_value = Mock()

        app = ConsumerApp(self.mock_config)
        app._running = True

        call_count = [0]

        def process_batch_side_effect():
            call_count[0] += 1
            if call_count[0] == 1:
                raise TimeoutError("Request timed out")
            else:
                app._running = False
                mock_result = Mock()
                mock_result.messages_processed = 0
                return mock_result

        # Act
        with patch.object(app, '_process_batch', side_effect=process_batch_side_effect):
            app._main_processing_loop()

        # Assert
        mock_sleep.assert_called()

    @patch('projects.can_data_platform.src.apps.consumer_app.SQSConsumerFactory')
    @patch('projects.can_data_platform.src.apps.consumer_app.MessageProcessorFactory')
    @patch('projects.can_data_platform.src.apps.consumer_app.LatencyTrackerFactory')
    @patch('projects.can_data_platform.src.apps.consumer_app.signal.signal')
    def test_handle_batch_errors_processing(self, mock_signal, mock_latency_factory,
                                           mock_processor_factory, mock_consumer_factory):
        """Test logging of processing errors in batch."""
        # Arrange
        mock_latency_factory.create_tracker.return_value = Mock()
        mock_processor_factory.create_processor.return_value = Mock()
        mock_consumer_factory.create_consumer.return_value = Mock()

        app = ConsumerApp(self.mock_config)

        mock_result = Mock()
        mock_result.errors = 3
        mock_result.deletion_errors = 0

        # Act
        with patch.object(app.logger, 'warning') as mock_warning:
            app._log_batch_errors(mock_result)

        # Assert
        mock_warning.assert_called_once_with("Encountered %s processing errors", 3)

    @patch('projects.can_data_platform.src.apps.consumer_app.SQSConsumerFactory')
    @patch('projects.can_data_platform.src.apps.consumer_app.MessageProcessorFactory')
    @patch('projects.can_data_platform.src.apps.consumer_app.LatencyTrackerFactory')
    @patch('projects.can_data_platform.src.apps.consumer_app.signal.signal')
    def test_handle_batch_errors_deletion(self, mock_signal, mock_latency_factory,
                                          mock_processor_factory, mock_consumer_factory):
        """Test logging of deletion errors in batch."""
        # Arrange
        mock_latency_factory.create_tracker.return_value = Mock()
        mock_processor_factory.create_processor.return_value = Mock()
        mock_consumer_factory.create_consumer.return_value = Mock()

        app = ConsumerApp(self.mock_config)

        mock_result = Mock()
        mock_result.errors = 0
        mock_result.deletion_errors = 2

        # Act
        with patch.object(app.logger, 'warning') as mock_warning:
            app._log_batch_errors(mock_result)

        # Assert
        mock_warning.assert_called_once_with("Encountered %s deletion errors", 2)

    @patch('projects.can_data_platform.src.apps.consumer_app.SQSConsumerFactory')
    @patch('projects.can_data_platform.src.apps.consumer_app.MessageProcessorFactory')
    @patch('projects.can_data_platform.src.apps.consumer_app.LatencyTrackerFactory')
    @patch('projects.can_data_platform.src.apps.consumer_app.signal.signal')
    def test_check_consumer_health_failure(self, mock_signal, mock_latency_factory,
                                           mock_processor_factory, mock_consumer_factory):
        """Test consumer health check failure."""
        # Arrange
        mock_latency_factory.create_tracker.return_value = Mock()
        mock_processor_factory.create_processor.return_value = Mock()
        mock_consumer = Mock()
        mock_consumer.health_check.return_value = False
        mock_consumer_factory.create_consumer.return_value = mock_consumer

        app = ConsumerApp(self.mock_config)
        app._running = True

        # Act
        with patch.object(app.logger, 'error') as mock_error:
            app._check_consumer_health()

        # Assert
        self.assertFalse(app._running)
        mock_error.assert_called_once_with("Consumer health check failed")

    @patch('projects.can_data_platform.src.apps.consumer_app.SQSConsumerFactory')
    @patch('projects.can_data_platform.src.apps.consumer_app.MessageProcessorFactory')
    @patch('projects.can_data_platform.src.apps.consumer_app.LatencyTrackerFactory')
    @patch('projects.can_data_platform.src.apps.consumer_app.signal.signal')
    def test_shutdown_with_io_error(self, mock_signal, mock_latency_factory,
                                    mock_processor_factory, mock_consumer_factory):
        """Test shutdown handles IOError during flush."""
        # Arrange
        mock_tracker = Mock()
        mock_tracker.flush.side_effect = IOError("Disk full")
        mock_latency_factory.create_tracker.return_value = mock_tracker
        mock_processor_factory.create_processor.return_value = Mock()
        mock_consumer_factory.create_consumer.return_value = Mock()

        app = ConsumerApp(self.mock_config)

        # Act
        with patch.object(app.logger, 'error') as mock_error:
            app._shutdown()

        # Assert
        mock_error.assert_any_call("Error flushing latency metrics: %s", mock_tracker.flush.side_effect)

    @patch('projects.can_data_platform.src.apps.consumer_app.SQSConsumerFactory')
    @patch('projects.can_data_platform.src.apps.consumer_app.MessageProcessorFactory')
    @patch('projects.can_data_platform.src.apps.consumer_app.LatencyTrackerFactory')
    @patch('projects.can_data_platform.src.apps.consumer_app.signal.signal')
    def test_shutdown_with_os_error(self, mock_signal, mock_latency_factory,
                                    mock_processor_factory, mock_consumer_factory):
        """Test shutdown handles OSError during flush."""
        # Arrange
        mock_tracker = Mock()
        mock_tracker.flush.side_effect = OSError("Permission denied")
        mock_latency_factory.create_tracker.return_value = mock_tracker
        mock_processor_factory.create_processor.return_value = Mock()
        mock_consumer_factory.create_consumer.return_value = Mock()

        app = ConsumerApp(self.mock_config)

        # Act
        with patch.object(app.logger, 'error') as mock_error:
            app._shutdown()

        # Assert
        mock_error.assert_any_call("Error flushing latency metrics: %s", mock_tracker.flush.side_effect)

    @patch('projects.can_data_platform.src.apps.consumer_app.SQSConsumerFactory')
    @patch('projects.can_data_platform.src.apps.consumer_app.MessageProcessorFactory')
    @patch('projects.can_data_platform.src.apps.consumer_app.LatencyTrackerFactory')
    @patch('projects.can_data_platform.src.apps.consumer_app.signal.signal')
    def test_handle_empty_batch_multiple_consecutive(self, mock_signal, mock_latency_factory,
                                                     mock_processor_factory, mock_consumer_factory):
        """Test handling multiple consecutive empty batches."""
        # Arrange
        mock_latency_factory.create_tracker.return_value = Mock()
        mock_processor_factory.create_processor.return_value = Mock()
        mock_consumer_factory.create_consumer.return_value = Mock()

        app = ConsumerApp(self.mock_config)
        app.consecutive_empty_batches = 2

        # Act
        with patch.object(app.logger, 'info') as mock_info:
            app._handle_empty_batch()

        # Assert
        self.assertEqual(app.consecutive_empty_batches, 3)
        # Should log suggestion message
        self.assertTrue(any('consecutive polls' in str(call) for call in mock_info.call_args_list))


if __name__ == '__main__':
    unittest.main(verbosity=2)