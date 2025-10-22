"""Unit tests for telemetry configuration management."""

import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from projects.can_data_platform.src.config.manager import (
    ConfigManager,
    TelemetryConfig,
)


class TestTelemetryConfig(unittest.TestCase):
    """Test TelemetryConfig data class and validation."""

    def setUp(self):
        """Set up test configuration."""
        self.valid_config_data = {
            "sqs_queue_url": "https://sqs.us-east-1.amazonaws.com/123456789/test-queue",
            "aws_region": "us-west-2",
            "sqs_batch_size": 5,
            "stream_interval": 0.1,
            "num_modules": 6,
            "voltage_range": (3500, 4000),
            "offset_range": (-20, 20),
            "default_output_path": "/tmp/test_output.jsonl",
        }

    def test_valid_configuration_creation(self):
        """Test creating valid configuration."""
        config = TelemetryConfig(**self.valid_config_data)
        
        assert config.sqs_queue_url == self.valid_config_data["sqs_queue_url"]
        assert config.aws_region == self.valid_config_data["aws_region"]
        assert config.sqs_batch_size == self.valid_config_data["sqs_batch_size"]
        assert config.stream_interval == pytest.approx(self.valid_config_data["stream_interval"])
        assert config.num_modules == self.valid_config_data["num_modules"]
        assert config.voltage_range == self.valid_config_data["voltage_range"]
        assert config.offset_range == self.valid_config_data["offset_range"]
        assert config.default_output_path == self.valid_config_data["default_output_path"]

    def test_config_with_none_queue_url(self):
        """Test configuration with None SQS queue URL."""
        config_data = self.valid_config_data.copy()
        config_data["sqs_queue_url"] = None
        config = TelemetryConfig(**config_data)
        
        assert config.sqs_queue_url is None
        config.validate()  # Should not raise

    def test_validation_success(self):
        """Test successful validation."""
        config = TelemetryConfig(**self.valid_config_data)
        # Should not raise any exception
        config.validate()

    def test_validation_batch_size_too_large(self):
        """Test validation with batch size too large."""
        config_data = self.valid_config_data.copy()
        config_data["sqs_batch_size"] = 11
        config = TelemetryConfig(**config_data)
        
        with pytest.raises(ValueError, match="SQS batch size cannot exceed 10"):
            config.validate()

    def test_validation_batch_size_too_small(self):
        """Test validation with batch size too small."""
        config_data = self.valid_config_data.copy()
        config_data["sqs_batch_size"] = 0
        config = TelemetryConfig(**config_data)
        
        with pytest.raises(ValueError, match="SQS batch size must be at least 1"):
            config.validate()

    def test_validation_batch_size_boundaries(self):
        """Test validation with batch size boundaries."""
        # Test minimum valid value
        config_data = self.valid_config_data.copy()
        config_data["sqs_batch_size"] = 1
        config = TelemetryConfig(**config_data)
        config.validate()  # Should not raise
        
        # Test maximum valid value
        config_data["sqs_batch_size"] = 10
        config = TelemetryConfig(**config_data)
        config.validate()  # Should not raise

    def test_validation_negative_stream_interval(self):
        """Test validation with negative stream interval."""
        config_data = self.valid_config_data.copy()
        config_data["stream_interval"] = -0.1
        config = TelemetryConfig(**config_data)
        
        with pytest.raises(ValueError, match="Stream interval cannot be negative"):
            config.validate()

    def test_validation_zero_stream_interval(self):
        """Test validation with zero stream interval (should be valid)."""
        config_data = self.valid_config_data.copy()
        config_data["stream_interval"] = 0.0
        config = TelemetryConfig(**config_data)
        config.validate()  # Should not raise

    def test_validation_invalid_num_modules(self):
        """Test validation with invalid number of modules."""
        config_data = self.valid_config_data.copy()
        config_data["num_modules"] = 0
        config = TelemetryConfig(**config_data)
        
        with pytest.raises(ValueError, match="Number of modules must be at least 1"):
            config.validate()

    def test_validation_negative_num_modules(self):
        """Test validation with negative number of modules."""
        config_data = self.valid_config_data.copy()
        config_data["num_modules"] = -1
        config = TelemetryConfig(**config_data)
        
        with pytest.raises(ValueError, match="Number of modules must be at least 1"):
            config.validate()


class TestConfigManager(unittest.TestCase):
    """Test ConfigManager configuration loading."""

    def setUp(self):
        """Set up test environment."""
        self.manager = ConfigManager(load_env=False)

    def test_initialization_with_env_loading(self):
        """Test manager initialization with environment loading."""
        with patch('projects.can_data_platform.src.config.manager.load_dotenv') as mock_load_dotenv:
            _ = ConfigManager(load_env=True)
            mock_load_dotenv.assert_called_once()

    def test_initialization_without_env_loading(self):
        """Test manager initialization without environment loading."""
        with patch('projects.can_data_platform.src.config.manager.load_dotenv') as mock_load_dotenv:
            _ = ConfigManager(load_env=False)
            mock_load_dotenv.assert_not_called()

    def test_load_config_with_defaults(self):
        """Test loading configuration with default values."""
        with patch.dict(os.environ, {}, clear=True):
            config = self.manager.load_config()
            
            assert config.sqs_queue_url is None
            assert config.aws_region == ConfigManager.DEFAULT_AWS_REGION
            assert config.sqs_batch_size == ConfigManager.DEFAULT_SQS_BATCH_SIZE
            assert config.stream_interval == pytest.approx(ConfigManager.DEFAULT_STREAM_INTERVAL)
            assert config.num_modules == ConfigManager.DEFAULT_NUM_MODULES
            assert config.voltage_range == ConfigManager.DEFAULT_VOLTAGE_RANGE
            assert config.offset_range == ConfigManager.DEFAULT_OFFSET_RANGE
            assert "sample_events_optimized.jsonl" in config.default_output_path

    def test_load_config_with_environment_variables(self):
        """Test loading configuration from environment variables."""
        env_vars = {
            "SQS_QUEUE_URL": "https://env-queue.amazonaws.com",
            "AWS_REGION": "eu-central-1",
            "SQS_BATCH_SIZE": "7",
            "PRODUCER_STREAM_INTERVAL": "0.2",
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = self.manager.load_config()
            
            assert config.sqs_queue_url == "https://env-queue.amazonaws.com"
            assert config.aws_region == "eu-central-1"
            assert config.sqs_batch_size == 7
            assert config.stream_interval == pytest.approx(0.2)

    def test_load_config_with_stream_interval_fallback(self):
        """Test loading configuration with STREAM_INTERVAL fallback."""
        env_vars = {
            "STREAM_INTERVAL": "0.15",
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = self.manager.load_config()
            
            assert config.stream_interval == pytest.approx(0.15)

    def test_load_config_producer_stream_interval_priority(self):
        """Test that PRODUCER_STREAM_INTERVAL takes priority over STREAM_INTERVAL."""
        env_vars = {
            "PRODUCER_STREAM_INTERVAL": "0.3",
            "STREAM_INTERVAL": "0.15",
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = self.manager.load_config()
            
            assert config.stream_interval == pytest.approx(0.3)

    def test_load_config_with_overrides(self):
        """Test loading configuration with parameter overrides."""
        with patch.dict(os.environ, {}, clear=True):
            config = self.manager.load_config(
                sqs_queue_url="https://override-queue.amazonaws.com",
                sqs_batch_size=3,
                stream_interval=0.75,
                num_modules=8,
            )
            
            assert config.sqs_queue_url == "https://override-queue.amazonaws.com"
            assert config.sqs_batch_size == 3
            assert config.stream_interval == pytest.approx(0.75)
            assert config.num_modules == 8
            # Other values should be defaults
            assert config.aws_region == ConfigManager.DEFAULT_AWS_REGION

    def test_load_config_overrides_take_precedence(self):
        """Test that overrides take precedence over environment variables."""
        env_vars = {
            "SQS_QUEUE_URL": "https://env-queue.amazonaws.com",
            "SQS_BATCH_SIZE": "8",
            "AWS_REGION": "eu-west-1",
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = self.manager.load_config(
                sqs_batch_size=3,  # Override env var
                aws_region="ap-southeast-1",  # Override env var
                num_modules=12,  # Override default
            )
            
            assert config.sqs_queue_url == "https://env-queue.amazonaws.com"  # From env
            assert config.sqs_batch_size == 3  # Override wins
            assert config.aws_region == "ap-southeast-1"  # Override wins
            assert config.num_modules == 12  # Override wins

    def test_load_config_validation_failure(self):
        """Test loading configuration with validation failure."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="SQS batch size cannot exceed 10"):
                self.manager.load_config(sqs_batch_size=15)

    def test_load_config_integer_conversion(self):
        """Test proper integer conversion from environment variables."""
        env_vars = {
            "SQS_BATCH_SIZE": "5",
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = self.manager.load_config()
            
            assert isinstance(config.sqs_batch_size, int)
            assert config.sqs_batch_size == 5

    def test_load_config_float_conversion(self):
        """Test proper float conversion from environment variables."""
        env_vars = {
            "PRODUCER_STREAM_INTERVAL": "0.125",
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = self.manager.load_config()
            
            assert isinstance(config.stream_interval, float)
            assert config.stream_interval == pytest.approx(0.125)

    def test_create_from_args_with_no_args(self):
        """Test creating configuration from args with no relevant attributes."""
        args = SimpleNamespace()
        
        with patch.dict(os.environ, {}, clear=True):
            config = ConfigManager.create_from_args(args)
            
            # Should use defaults
            assert config.sqs_batch_size == ConfigManager.DEFAULT_SQS_BATCH_SIZE
            # Use the actual default from load_config rather than constant
            default_config = ConfigManager().load_config()
            assert config.stream_interval == pytest.approx(default_config.stream_interval)
            assert "sample_events_optimized.jsonl" in config.default_output_path

    def test_create_from_args_with_all_args(self):
        """Test creating configuration from args with all relevant attributes."""
        args = SimpleNamespace(
            stream_interval=0.25,
            batch_size=6,
            output="/custom/output.jsonl",
        )
        
        with patch.dict(os.environ, {}, clear=True):
            config = ConfigManager.create_from_args(args)
            
            assert config.stream_interval == pytest.approx(0.25)
            assert config.sqs_batch_size == 6
            assert config.default_output_path == "/custom/output.jsonl"

    def test_create_from_args_with_batch_size_limit(self):
        """Test creating configuration with batch size limit enforced."""
        args = SimpleNamespace(
            batch_size=15,  # Exceeds limit
        )
        
        with patch.dict(os.environ, {}, clear=True):
            config = ConfigManager.create_from_args(args)
            
            # Should be capped at 10
            assert config.sqs_batch_size == 10

    def test_create_from_args_with_partial_args(self):
        """Test creating configuration from args with some attributes."""
        args = SimpleNamespace(
            stream_interval=0.4,
            # Missing batch_size, output
        )
        
        with patch.dict(os.environ, {}, clear=True):
            config = ConfigManager.create_from_args(args)
            
            assert config.stream_interval == pytest.approx(0.4)
            # Should use defaults for missing args
            assert config.sqs_batch_size == ConfigManager.DEFAULT_SQS_BATCH_SIZE
            assert "sample_events_optimized.jsonl" in config.default_output_path

    def test_create_from_args_with_none_values(self):
        """Test creating configuration from args with None values."""
        args = SimpleNamespace(
            stream_interval=None,
            batch_size=4,
            output=None,
        )
        
        with patch.dict(os.environ, {}, clear=True):
            config = ConfigManager.create_from_args(args)
            
            # None values should be ignored, defaults used
            default_config = ConfigManager().load_config()
            assert config.stream_interval == pytest.approx(default_config.stream_interval)
            assert "sample_events_optimized.jsonl" in config.default_output_path
            # Non-None values should be used
            assert config.sqs_batch_size == 4

    def test_default_output_path_construction(self):
        """Test that default output path is constructed correctly."""
        with patch.dict(os.environ, {}, clear=True):
            config = self.manager.load_config()
            
            assert config.default_output_path.endswith("sample_events_optimized.jsonl")
            assert "data" in config.default_output_path

    def test_config_with_custom_ranges(self):
        """Test configuration with custom voltage and offset ranges."""
        custom_voltage = (3000, 4500)
        custom_offset = (-100, 100)
        
        config = self.manager.load_config(
            voltage_range=custom_voltage,
            offset_range=custom_offset,
        )
        
        assert config.voltage_range == custom_voltage
        assert config.offset_range == custom_offset

    def test_default_constants_values(self):
        """Test that default constants have expected values."""
        assert ConfigManager.DEFAULT_AWS_REGION == "us-east-1"
        assert ConfigManager.DEFAULT_SQS_BATCH_SIZE == 10
        assert ConfigManager.DEFAULT_STREAM_INTERVAL == pytest.approx(0.05)
        assert ConfigManager.DEFAULT_NUM_MODULES == 4
        assert ConfigManager.DEFAULT_VOLTAGE_RANGE == (3400, 4150)
        assert ConfigManager.DEFAULT_OFFSET_RANGE == (-40, 40)
