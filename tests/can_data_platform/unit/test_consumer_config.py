"""Unit tests for consumer configuration management."""

import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from projects.can_data_platform.src.config.consumer_config import (
    ConsumerConfig,
    ConsumerConfigManager,
)


class TestConsumerConfig(unittest.TestCase):
    """Test ConsumerConfig data class and validation."""

    def setUp(self):
        """Set up test configuration."""
        self.valid_config_data = {
            "queue_url": "https://sqs.us-east-1.amazonaws.com/123456789/test-queue",
            "batch_size": 5,
            "poll_interval": 1.0,
            "max_retries": 3,
            "max_wait_time": 10,
            "aws_region": "us-west-2",
            "latency_flush_every": 50,
            "latency_output_dir": "/tmp/metrics",
            "sla_threshold_seconds": 3.0,
            "log_file": "/tmp/consumer.log",
            "log_level": "DEBUG",
        }

    def test_valid_configuration_creation(self):
        """Test creating valid configuration."""
        config = ConsumerConfig(**self.valid_config_data)
        
        assert config.queue_url == self.valid_config_data["queue_url"]
        assert config.batch_size == self.valid_config_data["batch_size"]
        assert config.poll_interval == self.valid_config_data["poll_interval"]
        assert config.max_retries == self.valid_config_data["max_retries"]
        assert config.max_wait_time == self.valid_config_data["max_wait_time"]
        assert config.aws_region == self.valid_config_data["aws_region"]
        assert config.latency_flush_every == self.valid_config_data["latency_flush_every"]
        assert config.latency_output_dir == self.valid_config_data["latency_output_dir"]
        assert config.sla_threshold_seconds == self.valid_config_data["sla_threshold_seconds"]
        assert config.log_file == self.valid_config_data["log_file"]
        assert config.log_level == self.valid_config_data["log_level"]

    def test_validation_success(self):
        """Test successful validation."""
        config = ConsumerConfig(**self.valid_config_data)
        # Should not raise any exception
        config.validate()

    def test_validation_empty_queue_url(self):
        """Test validation with empty queue URL."""
        config_data = self.valid_config_data.copy()
        config_data["queue_url"] = ""
        config = ConsumerConfig(**config_data)
        
        with pytest.raises(ValueError, match="SQS queue URL is required"):
            config.validate()

    def test_validation_none_queue_url(self):
        """Test validation with None queue URL."""
        config_data = self.valid_config_data.copy()
        config_data["queue_url"] = None
        config = ConsumerConfig(**config_data)
        
        with pytest.raises(ValueError, match="SQS queue URL is required"):
            config.validate()

    def test_validation_batch_size_too_small(self):
        """Test validation with batch size too small."""
        config_data = self.valid_config_data.copy()
        config_data["batch_size"] = 0
        config = ConsumerConfig(**config_data)
        
        with pytest.raises(ValueError, match="Batch size must be between 1 and 10"):
            config.validate()

    def test_validation_batch_size_too_large(self):
        """Test validation with batch size too large."""
        config_data = self.valid_config_data.copy()
        config_data["batch_size"] = 11
        config = ConsumerConfig(**config_data)
        
        with pytest.raises(ValueError, match="Batch size must be between 1 and 10"):
            config.validate()

    def test_validation_batch_size_boundaries(self):
        """Test validation with batch size boundaries."""
        # Test minimum valid value
        config_data = self.valid_config_data.copy()
        config_data["batch_size"] = 1
        config = ConsumerConfig(**config_data)
        config.validate()  # Should not raise
        
        # Test maximum valid value
        config_data["batch_size"] = 10
        config = ConsumerConfig(**config_data)
        config.validate()  # Should not raise

    def test_validation_negative_poll_interval(self):
        """Test validation with negative poll interval."""
        config_data = self.valid_config_data.copy()
        config_data["poll_interval"] = -1.0
        config = ConsumerConfig(**config_data)
        
        with pytest.raises(ValueError, match="Poll interval cannot be negative"):
            config.validate()

    def test_validation_zero_poll_interval(self):
        """Test validation with zero poll interval (should be valid)."""
        config_data = self.valid_config_data.copy()
        config_data["poll_interval"] = 0.0
        config = ConsumerConfig(**config_data)
        config.validate()  # Should not raise

    def test_validation_negative_max_retries(self):
        """Test validation with negative max retries."""
        config_data = self.valid_config_data.copy()
        config_data["max_retries"] = -1
        config = ConsumerConfig(**config_data)
        
        with pytest.raises(ValueError, match="Max retries cannot be negative"):
            config.validate()

    def test_validation_zero_max_retries(self):
        """Test validation with zero max retries (should be valid)."""
        config_data = self.valid_config_data.copy()
        config_data["max_retries"] = 0
        config = ConsumerConfig(**config_data)
        config.validate()  # Should not raise

    def test_validation_invalid_latency_flush_every(self):
        """Test validation with invalid latency flush interval."""
        config_data = self.valid_config_data.copy()
        config_data["latency_flush_every"] = 0
        config = ConsumerConfig(**config_data)
        
        with pytest.raises(ValueError, match="Latency flush interval must be at least 1"):
            config.validate()

    def test_validation_negative_latency_flush_every(self):
        """Test validation with negative latency flush interval."""
        config_data = self.valid_config_data.copy()
        config_data["latency_flush_every"] = -5
        config = ConsumerConfig(**config_data)
        
        with pytest.raises(ValueError, match="Latency flush interval must be at least 1"):
            config.validate()

    def test_validation_zero_sla_threshold(self):
        """Test validation with zero SLA threshold."""
        config_data = self.valid_config_data.copy()
        config_data["sla_threshold_seconds"] = 0.0
        config = ConsumerConfig(**config_data)
        
        with pytest.raises(ValueError, match="SLA threshold must be positive"):
            config.validate()

    def test_validation_negative_sla_threshold(self):
        """Test validation with negative SLA threshold."""
        config_data = self.valid_config_data.copy()
        config_data["sla_threshold_seconds"] = -1.0
        config = ConsumerConfig(**config_data)
        
        with pytest.raises(ValueError, match="SLA threshold must be positive"):
            config.validate()


class TestConsumerConfigManager(unittest.TestCase):
    """Test ConsumerConfigManager configuration loading."""

    def setUp(self):
        """Set up test environment."""
        self.manager = ConsumerConfigManager(load_env=False)

    def test_initialization_with_env_loading(self):
        """Test manager initialization with environment loading."""
        with patch('projects.can_data_platform.src.config.consumer_config.load_dotenv') as mock_load_dotenv:
            _ = ConsumerConfigManager(load_env=True)
            mock_load_dotenv.assert_called_once()

    def test_initialization_without_env_loading(self):
        """Test manager initialization without environment loading."""
        with patch('projects.can_data_platform.src.config.consumer_config.load_dotenv') as mock_load_dotenv:
            _ = ConsumerConfigManager(load_env=False)
            mock_load_dotenv.assert_not_called()

    def test_load_config_with_defaults(self):
        """Test loading configuration with default values."""
        with patch.dict(os.environ, {"SQS_QUEUE_URL": "https://test-queue.amazonaws.com"}, clear=True):
            config = self.manager.load_config()
            
            assert config.queue_url == "https://test-queue.amazonaws.com"
            assert config.batch_size == ConsumerConfigManager.DEFAULT_BATCH_SIZE
            assert config.poll_interval == ConsumerConfigManager.DEFAULT_POLL_INTERVAL
            assert config.max_retries == ConsumerConfigManager.DEFAULT_MAX_RETRIES
            assert config.max_wait_time == ConsumerConfigManager.DEFAULT_MAX_WAIT_TIME
            assert config.aws_region == ConsumerConfigManager.DEFAULT_AWS_REGION
            assert config.latency_flush_every == ConsumerConfigManager.DEFAULT_LATENCY_FLUSH_EVERY
            assert config.latency_output_dir == ConsumerConfigManager.DEFAULT_LATENCY_OUTPUT_DIR
            assert config.sla_threshold_seconds == ConsumerConfigManager.DEFAULT_SLA_THRESHOLD
            assert config.log_file is None
            assert config.log_level == ConsumerConfigManager.DEFAULT_LOG_LEVEL

    def test_load_config_with_environment_variables(self):
        """Test loading configuration from environment variables."""
        env_vars = {
            "SQS_QUEUE_URL": "https://env-queue.amazonaws.com",
            "SQS_BATCH_SIZE": "7",
            "SQS_CONSUMER_POLL_SEC": "2.5",
            "SQS_DELETION_MAX_RETRIES": "5",
            "SQS_WAIT_TIME_SECONDS": "15",
            "AWS_REGION": "eu-west-1",
            "LATENCY_FLUSH_EVERY": "75",
            "LATENCY_OUTPUT_DIR": "/custom/metrics",
            "SLA_THRESHOLD_SECONDS": "10.0",
            "CONSUMER_LOG_FILE": "/custom/consumer.log",
            "LOG_LEVEL": "WARNING",
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = self.manager.load_config()
            
            assert config.queue_url == "https://env-queue.amazonaws.com"
            assert config.batch_size == 7
            assert config.poll_interval == pytest.approx(2.5)
            assert config.max_retries == 5
            assert config.max_wait_time == 15
            assert config.aws_region == "eu-west-1"
            assert config.latency_flush_every == 75
            assert config.latency_output_dir == "/custom/metrics"
            assert config.sla_threshold_seconds == pytest.approx(10.0)
            assert config.log_file == "/custom/consumer.log"
            assert config.log_level == "WARNING"

    def test_load_config_with_overrides(self):
        """Test loading configuration with parameter overrides."""
        with patch.dict(os.environ, {"SQS_QUEUE_URL": "https://test-queue.amazonaws.com"}, clear=True):
            config = self.manager.load_config(
                batch_size=3,
                poll_interval=0.5,
                max_retries=2,
                log_level="ERROR",
            )
            
            assert config.queue_url == "https://test-queue.amazonaws.com"
            assert config.batch_size == 3
            assert config.poll_interval == pytest.approx(0.5)
            assert config.max_retries == 2
            assert config.log_level == "ERROR"
            # Other values should be defaults
            assert config.aws_region == ConsumerConfigManager.DEFAULT_AWS_REGION

    def test_load_config_overrides_take_precedence(self):
        """Test that overrides take precedence over environment variables."""
        env_vars = {
            "SQS_QUEUE_URL": "https://env-queue.amazonaws.com",
            "SQS_BATCH_SIZE": "8",
            "LOG_LEVEL": "DEBUG",
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = self.manager.load_config(
                batch_size=3,  # Override env var
                log_level="ERROR",  # Override env var
                aws_region="ap-south-1",  # Override default
            )
            
            assert config.queue_url == "https://env-queue.amazonaws.com"  # From env
            assert config.batch_size == 3  # Override wins
            assert config.log_level == "ERROR"  # Override wins
            assert config.aws_region == "ap-south-1"  # Override wins

    def test_load_config_validation_failure(self):
        """Test loading configuration with validation failure."""
        with patch.dict(os.environ, {"SQS_QUEUE_URL": ""}, clear=True):
            with pytest.raises(ValueError, match="SQS queue URL is required"):
                self.manager.load_config()

    def test_load_config_integer_conversion(self):
        """Test proper integer conversion from environment variables."""
        env_vars = {
            "SQS_QUEUE_URL": "https://test-queue.amazonaws.com",
            "SQS_BATCH_SIZE": "5",
            "SQS_DELETION_MAX_RETRIES": "3",
            "SQS_WAIT_TIME_SECONDS": "20",
            "LATENCY_FLUSH_EVERY": "100",
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = self.manager.load_config()
            
            assert isinstance(config.batch_size, int)
            assert isinstance(config.max_retries, int)
            assert isinstance(config.max_wait_time, int)
            assert isinstance(config.latency_flush_every, int)

    def test_load_config_float_conversion(self):
        """Test proper float conversion from environment variables."""
        env_vars = {
            "SQS_QUEUE_URL": "https://test-queue.amazonaws.com",
            "SQS_CONSUMER_POLL_SEC": "1.5",
            "SLA_THRESHOLD_SECONDS": "7.5",
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = self.manager.load_config()
            
            assert isinstance(config.poll_interval, float)
            assert isinstance(config.sla_threshold_seconds, float)
            assert config.poll_interval == pytest.approx(1.5)
            assert config.sla_threshold_seconds == pytest.approx(7.5)

    def test_create_from_args_with_no_args(self):
        """Test creating configuration from args with no relevant attributes."""
        args = SimpleNamespace()
        
        with patch.dict(os.environ, {"SQS_QUEUE_URL": "https://test-queue.amazonaws.com"}, clear=True):
            config = ConsumerConfigManager.create_from_args(args)
            
            # Should use defaults
            assert config.batch_size == ConsumerConfigManager.DEFAULT_BATCH_SIZE
            assert config.poll_interval == ConsumerConfigManager.DEFAULT_POLL_INTERVAL
            assert config.max_retries == ConsumerConfigManager.DEFAULT_MAX_RETRIES
            assert config.log_level == ConsumerConfigManager.DEFAULT_LOG_LEVEL

    def test_create_from_args_with_all_args(self):
        """Test creating configuration from args with all relevant attributes."""
        args = SimpleNamespace(
            batch_size=4,
            poll_interval=2.0,
            max_retries=6,
            log_level="debug",
            latency_flush=150,
        )
        
        with patch.dict(os.environ, {"SQS_QUEUE_URL": "https://test-queue.amazonaws.com"}, clear=True):
            config = ConsumerConfigManager.create_from_args(args)
            
            assert config.batch_size == 4
            assert config.poll_interval == pytest.approx(2.0)
            assert config.max_retries == 6
            assert config.log_level == "DEBUG"  # Should be uppercased
            assert config.latency_flush_every == 150

    def test_create_from_args_with_partial_args(self):
        """Test creating configuration from args with some attributes."""
        args = SimpleNamespace(
            batch_size=6,
            log_level="warning",
            # Missing poll_interval, max_retries, latency_flush
        )
        
        with patch.dict(os.environ, {"SQS_QUEUE_URL": "https://test-queue.amazonaws.com"}, clear=True):
            config = ConsumerConfigManager.create_from_args(args)
            
            assert config.batch_size == 6
            assert config.log_level == "WARNING"
            # Should use defaults for missing args
            assert config.poll_interval == ConsumerConfigManager.DEFAULT_POLL_INTERVAL
            assert config.max_retries == ConsumerConfigManager.DEFAULT_MAX_RETRIES
            assert config.latency_flush_every == ConsumerConfigManager.DEFAULT_LATENCY_FLUSH_EVERY

    def test_create_from_args_with_none_values(self):
        """Test creating configuration from args with None values."""
        args = SimpleNamespace(
            batch_size=None,
            poll_interval=2.0,
            max_retries=None,
            log_level=None,
            latency_flush=50,
        )
        
        with patch.dict(os.environ, {"SQS_QUEUE_URL": "https://test-queue.amazonaws.com"}, clear=True):
            config = ConsumerConfigManager.create_from_args(args)
            
            # None values should be ignored, defaults used
            assert config.batch_size == ConsumerConfigManager.DEFAULT_BATCH_SIZE
            assert config.max_retries == ConsumerConfigManager.DEFAULT_MAX_RETRIES
            assert config.log_level == ConsumerConfigManager.DEFAULT_LOG_LEVEL
            # Non-None values should be used
            assert config.poll_interval == pytest.approx(2.0)
            assert config.latency_flush_every == 50

    def test_create_from_args_case_insensitive_log_level(self):
        """Test that log level is properly uppercased."""
        test_cases = ["debug", "INFO", "Warning", "ERROR", "critical"]
        expected = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        
        for input_level, expected_level in zip(test_cases, expected):
            args = SimpleNamespace(log_level=input_level)
            
            with patch.dict(os.environ, {"SQS_QUEUE_URL": "https://test-queue.amazonaws.com"}, clear=True):
                config = ConsumerConfigManager.create_from_args(args)
                assert config.log_level == expected_level