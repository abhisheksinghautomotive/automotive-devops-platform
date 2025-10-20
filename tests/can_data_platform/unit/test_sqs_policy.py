"""Unit tests for SQS policy module."""

import sys
from pathlib import Path


def setup_project_path():
    """Add project root to Python path for module imports."""
    project_root = Path(__file__).parent.parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))


# Setup path before importing project modules
setup_project_path()

from projects.can_data_platform.src.sqs.policy import (  # noqa: E402
    sqs_consumer_policy,
    sqs_producer_policy,
)


class TestSQSPolicyFunctions:
    """Test cases for SQS IAM policy generation functions."""

    def test_sqs_producer_policy_structure(self):
        """Test producer policy structure and content."""
        queue_arn = "arn:aws:sqs:us-east-1:123456789012:test-queue"

        policy = sqs_producer_policy(queue_arn)

        # Verify basic structure
        assert isinstance(policy, dict)
        assert policy["Version"] == "2012-10-17"
        assert "Statement" in policy
        assert len(policy["Statement"]) == 1

        # Verify statement content
        statement = policy["Statement"][0]
        assert statement["Sid"] == "AllowSQSPublish"
        assert statement["Effect"] == "Allow"
        assert statement["Resource"] == queue_arn

        # Verify actions
        expected_actions = [
            "sqs:SendMessage",
            "sqs:GetQueueUrl",
            "sqs:GetQueueAttributes",
        ]
        assert statement["Action"] == expected_actions

    def test_sqs_consumer_policy_structure(self):
        """Test consumer policy structure and content."""
        queue_arn = "arn:aws:sqs:us-east-1:123456789012:test-queue"

        policy = sqs_consumer_policy(queue_arn)

        # Verify basic structure
        assert isinstance(policy, dict)
        assert policy["Version"] == "2012-10-17"
        assert "Statement" in policy
        assert len(policy["Statement"]) == 1

        # Verify statement content
        statement = policy["Statement"][0]
        assert statement["Sid"] == "AllowSQSConsume"
        assert statement["Effect"] == "Allow"
        assert statement["Resource"] == queue_arn

        # Verify actions
        expected_actions = [
            "sqs:ReceiveMessage",
            "sqs:DeleteMessage",
            "sqs:GetQueueAttributes",
            "sqs:GetQueueUrl",
        ]
        assert statement["Action"] == expected_actions

    def test_producer_policy_different_arns(self):
        """Test producer policy with different ARN formats."""
        test_cases = [
            "arn:aws:sqs:us-west-2:987654321098:production-queue",
            "arn:aws:sqs:eu-west-1:111122223333:dev-telemetry-queue",
            "arn:aws:sqs:ap-south-1:444455556666:staging-can-data",
        ]

        for queue_arn in test_cases:
            policy = sqs_producer_policy(queue_arn)
            assert policy["Statement"][0]["Resource"] == queue_arn

    def test_consumer_policy_different_arns(self):
        """Test consumer policy with different ARN formats."""
        test_cases = [
            "arn:aws:sqs:us-west-2:987654321098:production-queue",
            "arn:aws:sqs:eu-west-1:111122223333:dev-telemetry-queue",
            "arn:aws:sqs:ap-south-1:444455556666:staging-can-data",
        ]

        for queue_arn in test_cases:
            policy = sqs_consumer_policy(queue_arn)
            assert policy["Statement"][0]["Resource"] == queue_arn

    def test_policy_json_serializable(self):
        """Test that policies are JSON serializable."""
        import json

        queue_arn = "arn:aws:sqs:us-east-1:123456789012:test-queue"

        producer_policy = sqs_producer_policy(queue_arn)
        consumer_policy = sqs_consumer_policy(queue_arn)

        # Should not raise exceptions
        json.dumps(producer_policy)
        json.dumps(consumer_policy)

    def test_producer_consumer_policy_differences(self):
        """Test differences between producer and consumer policies."""
        queue_arn = "arn:aws:sqs:us-east-1:123456789012:test-queue"

        producer_policy = sqs_producer_policy(queue_arn)
        consumer_policy = sqs_consumer_policy(queue_arn)

        producer_actions = set(producer_policy["Statement"][0]["Action"])
        consumer_actions = set(consumer_policy["Statement"][0]["Action"])

        # Producer should have SendMessage, consumer should not
        assert "sqs:SendMessage" in producer_actions
        assert "sqs:SendMessage" not in consumer_actions

        # Consumer should have ReceiveMessage and DeleteMessage, producer should not
        assert "sqs:ReceiveMessage" in consumer_actions
        assert "sqs:DeleteMessage" in consumer_actions
        assert "sqs:ReceiveMessage" not in producer_actions
        assert "sqs:DeleteMessage" not in producer_actions

        # Both should have common actions
        common_actions = {"sqs:GetQueueUrl", "sqs:GetQueueAttributes"}
        assert common_actions.issubset(producer_actions)
        assert common_actions.issubset(consumer_actions)

    def test_policy_sid_uniqueness(self):
        """Test that policy SIDs are unique and descriptive."""
        queue_arn = "arn:aws:sqs:us-east-1:123456789012:test-queue"

        producer_policy = sqs_producer_policy(queue_arn)
        consumer_policy = sqs_consumer_policy(queue_arn)

        producer_sid = producer_policy["Statement"][0]["Sid"]
        consumer_sid = consumer_policy["Statement"][0]["Sid"]

        assert producer_sid == "AllowSQSPublish"
        assert consumer_sid == "AllowSQSConsume"
        assert producer_sid != consumer_sid
