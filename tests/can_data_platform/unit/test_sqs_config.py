"""Unit tests for SQS configuration module."""

import os
import sys
from pathlib import Path

import pytest


def setup_project_path():
    """Add project root to Python path for module imports."""
    project_root = Path(__file__).parent.parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))


# Setup path before importing project modules
setup_project_path()

from projects.can_data_platform.src.sqs.config import SQSQueueConfig  # noqa: E402


class TestSQSQueueConfig:
    """Test cases for SQSQueueConfig dataclass."""

    def test_default_values(self):
        """Test SQSQueueConfig with default values."""
        config = SQSQueueConfig(queue_name="test-queue")

        assert config.queue_name == "test-queue"
        assert config.region == "us-east-1"
        assert config.visibility_timeout == 30
        assert config.message_retention_seconds == 345600
        assert config.encrypt is False
        assert config.wait_time_seconds == 20
        assert config.max_message_size == 262144

    def test_custom_values(self):
        """Test SQSQueueConfig with custom values."""
        config = SQSQueueConfig(
            queue_name="custom-queue",
            region="us-west-2",
            visibility_timeout=60,
            message_retention_seconds=86400,
            encrypt=True,
            wait_time_seconds=10,
            max_message_size=131072,
        )

        assert config.queue_name == "custom-queue"
        assert config.region == "us-west-2"
        assert config.visibility_timeout == 60
        assert config.message_retention_seconds == 86400
        assert config.encrypt is True
        assert config.wait_time_seconds == 10
        assert config.max_message_size == 131072

    def test_from_environment_variables(self, monkeypatch):
        """Test SQSQueueConfig creation from environment variables."""
        # Set environment variables
        monkeypatch.setenv("SQS_QUEUE_NAME", "env-queue")
        monkeypatch.setenv("AWS_REGION", "eu-west-1")
        monkeypatch.setenv("SQS_VISIBILITY_TIMEOUT", "45")
        monkeypatch.setenv("SQS_MESSAGE_RETENTION_SECONDS", "172800")

        config = SQSQueueConfig(
            queue_name=os.getenv("SQS_QUEUE_NAME", "default"),
            region=os.getenv("AWS_REGION", "us-east-1"),
            visibility_timeout=int(os.getenv("SQS_VISIBILITY_TIMEOUT", "30")),
            message_retention_seconds=int(
                os.getenv("SQS_MESSAGE_RETENTION_SECONDS", "345600")
            ),
        )

        assert config.queue_name == "env-queue"
        assert config.region == "eu-west-1"
        assert config.visibility_timeout == 45
        assert config.message_retention_seconds == 172800

    def test_queue_name_required(self):
        """Test that queue_name is required."""
        with pytest.raises(
            TypeError, match="missing 1 required positional argument: 'queue_name'"
        ):
            SQSQueueConfig()  # pylint: disable=no-value-for-parameter

    def test_encryption_boolean(self):
        """Test encryption parameter accepts boolean values."""
        config_false = SQSQueueConfig(queue_name="test", encrypt=False)
        config_true = SQSQueueConfig(queue_name="test", encrypt=True)

        assert config_false.encrypt is False
        assert config_true.encrypt is True

    def test_numeric_constraints(self):
        """Test numeric field constraints."""
        config = SQSQueueConfig(
            queue_name="test",
            visibility_timeout=1,
            message_retention_seconds=60,
            wait_time_seconds=0,
            max_message_size=1024,
        )

        assert config.visibility_timeout == 1
        assert config.message_retention_seconds == 60
        assert config.wait_time_seconds == 0
        assert config.max_message_size == 1024
