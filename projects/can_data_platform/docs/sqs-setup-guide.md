# AWS SQS Queue Setup Guide

**Issue**: #69 - Set Up AWS SQS Queue (Development Environment)
**Author**: Abhishek Singh
**Date**: October 19, 2025
**Status**: Implementation Guide

---

## Overview

This guide provides step-by-step instructions for setting up an AWS SQS Standard Queue for the automotive telemetry data pipeline. The queue acts as a buffer between the FastAPI receiver and the batch consumer, enabling decoupled, scalable message processing.

---

## Prerequisites

### 1. AWS Account
- Active AWS account (Free Tier sufficient for development)
- Access to SQS service

### 2. AWS CLI Installed
```bash
# Check if AWS CLI is installed
aws --version

# If not installed:
# macOS
brew install awscli

# Linux
pip install awscli

# Windows
# Download installer from: https://aws.amazon.com/cli/
```

### 3. AWS Credentials Configured
```bash
# Configure AWS credentials
aws configure

# Provide:
# - AWS Access Key ID
# - AWS Secret Access Key
# - Default region (us-east-1)
# - Default output format (json)
```

### 4. Required IAM Permissions
Your IAM user/role needs the following permissions:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "sqs:CreateQueue",
        "sqs:GetQueueUrl",
        "sqs:GetQueueAttributes",
        "sqs:SetQueueAttributes",
        "sqs:TagQueue",
        "sqs:SendMessage",
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage"
      ],
      "Resource": "arn:aws:sqs:us-east-1:*:telemetry-queue-*"
    }
  ]
}
```

### 5. Python Dependencies
```bash
pip install boto3
```

---

## Queue Configuration

### Design Decisions (from ADR 0001)

**Queue Type**: Standard (not FIFO)

**Rationale**:
- **Cost**: $0.40/million requests (vs $0.50/million for FIFO)
- **Throughput**: Unlimited (vs 3,000 msg/sec for FIFO)
- **Ordering**: Not required for analytics use case
- **Duplicates**: Acceptable (<0.1% expected, handled downstream)

**Configuration Parameters**:

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Message Retention | 4 days (345,600s) | Allow recovery from consumer outages |
| Visibility Timeout | 30 seconds | Allow processing before re-queue |
| Long Polling | 20 seconds | Reduce empty receives (cost optimization) |
| Max Message Size | 256 KB | Sufficient for telemetry payload |
| Encryption | Optional (SSE) | Enable for production environments |

---

## Setup Instructions

### Method 1: Using Provided Script (Recommended)

#### Step 1: Place Script in Repository
```bash
cd automotive-devops-platform
mkdir -p scripts
cp setup_sqs.py scripts/
chmod +x scripts/setup_sqs.py
```

#### Step 2: Run Setup Script
```bash
# Basic setup with default settings
python scripts/setup_sqs.py

# With custom options
python scripts/setup_sqs.py \
  --queue-name telemetry-queue-dev \
  --region us-east-1 \
  --encrypt \
  --output-env \
  --output-iam
```

#### Step 3: Verify Output
The script will:
1. Create the SQS queue
2. Display queue URL and ARN
3. Send a test message
4. Receive and delete the test message
5. Output configuration files (if requested)

**Expected Output**:
```
================================================================================
Creating SQS Queue: telemetry-queue-dev
================================================================================

Creating queue in region: us-east-1
Configuration:
  - Message Retention: 345600s (4.0 days)
  - Visibility Timeout: 30s
  - Long Polling: 20s
  - Max Message Size: 256 KB

✅ Queue created successfully!
Queue URL: https://sqs.us-east-1.amazonaws.com/123456789012/telemetry-queue-dev
Queue ARN: arn:aws:sqs:us-east-1:123456789012:telemetry-queue-dev

================================================================================
TESTING MESSAGE FLOW
================================================================================
Sending test message...
✅ Test message sent successfully!
Message ID: 12345678-1234-1234-1234-123456789012

Receiving test message...
✅ Test message received!
Vehicle ID: test-vehicle-001
✅ Test message deleted

================================================================================
SQS QUEUE SETUP SUMMARY
================================================================================

✅ Queue Name: telemetry-queue-dev
✅ Region: us-east-1
✅ Queue URL: https://sqs.us-east-1.amazonaws.com/123456789012/telemetry-queue-dev
✅ Queue ARN: arn:aws:sqs:us-east-1:123456789012:telemetry-queue-dev
```

---

### Method 2: Using AWS Console (Manual)

#### Step 1: Navigate to SQS Console
1. Log in to AWS Console
2. Navigate to SQS service
3. Click "Create queue"

#### Step 2: Configure Queue
**Type**: Standard (not FIFO)

**Basic Configuration**:
- Name: `telemetry-queue-dev`
- Visibility timeout: 30 seconds
- Message retention period: 4 days
- Delivery delay: 0 seconds
- Maximum message size: 256 KB
- Receive message wait time: 20 seconds (long polling)

**Encryption** (Optional):
- Server-side encryption: Enable (SQS managed keys)

**Access Policy** (Optional):
- Use default (private queue)

**Tags**:
- Project: automotive-devops-platform
- Component: can-data-pipeline
- Environment: development

#### Step 3: Create Queue
Click "Create queue" and note the Queue URL

---

### Method 3: Using AWS CLI

```bash
# Create queue
aws sqs create-queue \
  --queue-name telemetry-queue-dev \
  --attributes \
    MessageRetentionPeriod=345600,\
    VisibilityTimeout=30,\
    ReceiveMessageWaitTimeSeconds=20,\
    MaximumMessageSize=262144 \
  --tags \
    Project=automotive-devops-platform \
    Component=can-data-pipeline \
    Environment=development

# Get queue URL
aws sqs get-queue-url --queue-name telemetry-queue-dev

# Get queue attributes
aws sqs get-queue-attributes \
  --queue-url <QUEUE_URL> \
  --attribute-names All
```

---

## Configuration Files

### 1. Environment Variables (.env)

Add the following to your `.env` file:

```bash
# AWS SQS Configuration
AWS_REGION=us-east-1
SQS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/123456789012/telemetry-queue-dev
SQS_QUEUE_NAME=telemetry-queue-dev

# SQS Client Configuration
SQS_MAX_MESSAGES=100
SQS_WAIT_TIME_SECONDS=20
SQS_VISIBILITY_TIMEOUT=30
```

### 2. IAM Policy for Producer (FastAPI Receiver)

Save as `iam-policies/sqs-producer-policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowSQSPublish",
      "Effect": "Allow",
      "Action": [
        "sqs:SendMessage",
        "sqs:GetQueueUrl",
        "sqs:GetQueueAttributes"
      ],
      "Resource": "arn:aws:sqs:us-east-1:ACCOUNT_ID:telemetry-queue-dev"
    }
  ]
}
```

### 3. IAM Policy for Consumer (Batch Processor)

Save as `iam-policies/sqs-consumer-policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowSQSConsume",
      "Effect": "Allow",
      "Action": [
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "sqs:GetQueueAttributes",
        "sqs:GetQueueUrl"
      ],
      "Resource": "arn:aws:sqs:us-east-1:ACCOUNT_ID:telemetry-queue-dev"
    }
  ]
}
```

---

## Validation & Testing

### Test 1: Send Message via AWS CLI
```bash
# Send test message
aws sqs send-message \
  --queue-url <YOUR_QUEUE_URL> \
  --message-body '{"vehicle_id": "test-001", "timestamp": "2025-10-19T19:00:00Z"}'

# Verify message sent
# Check output for MessageId
```

### Test 2: Receive Message via AWS CLI
```bash
# Receive message (long poll)
aws sqs receive-message \
  --queue-url <YOUR_QUEUE_URL> \
  --max-number-of-messages 1 \
  --wait-time-seconds 20

# Delete message after receiving
aws sqs delete-message \
  --queue-url <YOUR_QUEUE_URL> \
  --receipt-handle <RECEIPT_HANDLE>
```

### Test 3: Python Validation Script

Create `scripts/test_sqs_connection.py`:

```python
import boto3
import json
from datetime import datetime

def test_sqs_connection(queue_url):
    """Test SQS queue connectivity."""
    sqs = boto3.client('sqs', region_name='us-east-1')

    # Send test message
    test_msg = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "vehicle_id": "test-vehicle-001",
        "test": True
    }

    print(f"Sending test message to: {queue_url}")
    response = sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps(test_msg)
    )
    print(f"✅ Message sent. ID: {response['MessageId']}")

    # Receive test message
    print("\nReceiving message...")
    response = sqs.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=1,
        WaitTimeSeconds=20
    )

    if 'Messages' in response:
        msg = response['Messages'][0]
        print(f"✅ Message received. ID: {msg['MessageId']}")

        # Delete message
        sqs.delete_message(
            QueueUrl=queue_url,
            ReceiptHandle=msg['ReceiptHandle']
        )
        print("✅ Message deleted")
        print("\n✅ SQS connection test passed!")
    else:
        print("⚠️  No messages received")

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: python test_sqs_connection.py <QUEUE_URL>")
        sys.exit(1)

    test_sqs_connection(sys.argv[1])
```

Run test:
```bash
python scripts/test_sqs_connection.py <YOUR_QUEUE_URL>
```

---

## Monitoring & Observability

### CloudWatch Metrics (Automatic)

AWS automatically publishes the following metrics for your queue:

**Key Metrics**:
- `ApproximateNumberOfMessages` - Messages available
- `ApproximateNumberOfMessagesNotVisible` - In-flight messages
- `NumberOfMessagesSent` - Messages published
- `NumberOfMessagesReceived` - Messages consumed
- `NumberOfMessagesDeleted` - Successfully processed
- `ApproximateAgeOfOldestMessage` - Queue backlog age

### View Metrics in Console
1. Go to SQS Console
2. Select your queue
3. Click "Monitoring" tab
4. View real-time metrics

### Create CloudWatch Alarm (Optional)

```bash
# Alert when queue depth > 1000 messages
aws cloudwatch put-metric-alarm \
  --alarm-name telemetry-queue-depth-high \
  --alarm-description "Alert when queue depth exceeds 1000" \
  --metric-name ApproximateNumberOfMessages \
  --namespace AWS/SQS \
  --statistic Average \
  --period 300 \
  --evaluation-periods 2 \
  --threshold 1000 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=QueueName,Value=telemetry-queue-dev
```

---

## Cost Estimation

### Development Environment (MVP)

**Assumptions**:
- 50 messages/second
- 24/7 operation
- 30 days/month

**Calculations**:
- Total requests: 50 msg/s × 86,400 s/day × 30 days = 129,600,000 requests
- Long polling reduces empty receives by ~95%
- Effective billable requests: ~130M

**Cost**:
- SQS Standard: $0.40 per 1M requests
- Monthly cost: 130M × $0.40/M = **$52/month**

**Cost Optimization**:
- Long polling (20s): Saves ~95% on empty receive costs
- Batch operations: Reduces API calls
- Standard queue: 20% cheaper than FIFO

---

## Troubleshooting

### Issue: "AccessDenied" Error

**Cause**: Insufficient IAM permissions

**Solution**:
1. Check IAM user/role has SQS permissions
2. Verify resource ARN matches queue ARN
3. Attach appropriate IAM policy (see templates above)

### Issue: Queue Not Created

**Cause**: Region mismatch or naming conflict

**Solution**:
```bash
# Check if queue exists in different region
aws sqs list-queues --region us-east-1

# Try different queue name
python scripts/setup_sqs.py --queue-name telemetry-queue-dev-v2
```

### Issue: Messages Not Received

**Cause**: Visibility timeout or polling configuration

**Solution**:
```bash
# Check queue attributes
aws sqs get-queue-attributes \
  --queue-url <QUEUE_URL> \
  --attribute-names All

# Ensure ReceiveMessageWaitTimeSeconds = 20 (long polling)
```

### Issue: High Costs

**Cause**: Too many empty receives (short polling)

**Solution**:
- Verify long polling enabled (20s wait time)
- Check ReceiveMessageWaitTimeSeconds attribute
- Use batch receive operations

---

## Security Best Practices

### 1. Least Privilege IAM Policies
- Use specific resource ARNs (not wildcards)
- Separate producer and consumer policies
- Rotate access keys regularly

### 2. Encryption
```bash
# Enable server-side encryption
python scripts/setup_sqs.py --encrypt
```

### 3. Access Control
- Queue is private by default
- Do not make queue publicly accessible
- Use IAM roles for EC2/ECS (not access keys)

### 4. Monitoring
- Enable CloudWatch alarms for queue depth
- Monitor failed message deliveries
- Track message age

---

## Next Steps (After Issue #69)

1. **Issue #70**: Implement SQS publisher in FastAPI receiver
   - Add boto3 SQS client to FastAPI app
   - Publish messages to queue after validation
   - Handle publish errors gracefully

2. **Issue #71**: Build SQS batch consumer
   - Poll queue with long polling
   - Process messages in batches
   - Write to JSONL files
   - Delete messages after success

3. **Issue #72**: Add end-to-end latency tracking
   - Measure queue latency
   - Log P50/P95/P99 metrics
   - Track processing time

---

## References

- **AWS SQS Documentation**: https://docs.aws.amazon.com/sqs/
- **boto3 SQS Reference**: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sqs.html
- **ADR 0001**: docs/adr/0001-ingestion-transport.md
- **Issue #69**: GitHub issue tracking

---

## Acceptance Criteria Checklist

- [ ] SQS Standard queue created in us-east-1
- [ ] Queue configured with 4-day retention
- [ ] Long polling enabled (20s)
- [ ] Visibility timeout set to 30s
- [ ] Queue URL saved to .env file
- [ ] IAM policies generated (producer + consumer)
- [ ] Test message sent successfully
- [ ] Test message received and deleted
- [ ] CloudWatch metrics visible
- [ ] Documentation complete

---

**Status**: Ready for Implementation
**Estimated Time**: 1-2 hours
**Closes Issue**: #69
