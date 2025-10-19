# Project 01: Cloud-Native Automotive Telemetry Platform

> **Build a production-grade, scalable telemetry data pipeline that ingests, processes, and analyzes automotive CAN bus data at scale - demonstrating system design, cloud-native DevOps practices, and interview-ready technical storytelling.**

---

## 📊 Project Status

**Milestone**: P01-Core-Pipeline-MVP (Due: Oct 26, 2025)  
**Progress**: 0/8 issues complete (just started)  
**Test Coverage**: 96% (maintained)  
**Latest Update**: Oct 19, 2025

---

## 🎯 MVP Goal

Build a **minimal viable complete system** demonstrating:

```
Simulated Telemetry → FastAPI Ingest → SQS Buffer → Batch Consumer → JSONL Files → Aggregation
                                                                              ↓
                                                                          AWS S3 (Week 2)
```

**Success Criteria**:
- ✅ Process **1,000+ synthetic messages** with zero data loss
- ✅ **P95 latency < 5 seconds** (ingest → persist)
- ✅ Generate **hourly aggregate** output (count per vehicle)
- ✅ Maintain **≥95% test coverage**
- ✅ **ADR 0001** (SQS Transport) marked as "Accepted"

---

## 🏗️ Architecture Overview

### Current Architecture (Week 1 - MVP)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Battery Simulator (src/generator/)                                     │
│  - Realistic physics-based model                                         │
│  - Module-to-module variance                                             │
│  - 200ms sampling rate                                                   │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │ HTTP POST
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  FastAPI Receiver (src/receiver/)                                        │
│  - /ingest endpoint (POST)                                               │
│  - API key authentication (X-API-Key header)                             │
│  - Pydantic validation                                                   │
│  - Async request handling                                                │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │ Publish to Queue
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  AWS SQS Standard Queue                                                  │
│  - Message buffering & decoupling                                        │
│  - Long polling (20s WaitTimeSeconds)                                    │
│  - 30s visibility timeout                                                │
│  - Dead Letter Queue (DLQ) - future                                      │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │ Poll (100 msgs OR 2s timeout)
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Batch Consumer (src/consumer/)                                          │
│  - Async SQS polling                                                     │
│  - Batch processing (100 msgs OR 2s timeout)                             │
│  - Time-partitioned JSONL output                                         │
│  - Latency tracking (P50/P95/P99)                                        │
│  - Message deletion after success                                        │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │ Write batches
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Local Storage (data/raw/)                                               │
│  Path: year=YYYY/month=MM/day=DD/hour=HH/batch-<timestamp>.jsonl        │
│  - Line-delimited JSON                                                   │
│  - Human-readable format                                                 │
│  - Time-partitioned for efficient querying                               │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │ Read batches
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Aggregator (src/aggregator/)                                            │
│  - Hourly aggregation script                                             │
│  - Count per vehicle                                                     │
│  - Basic statistics (min/max/avg)                                        │
│  - Output: aggregated-<timestamp>.json                                   │
└─────────────────────────────────────────────────────────────────────────┘
```

### Future Architecture (Week 2 - S3 Integration)

- Replace local JSONL with **AWS S3** uploads
- Add **S3 lifecycle policies**: Standard (7d) → IA (30d) → Glacier (90d)
- Cost optimization: ~$23/month → ~$5/month for 1TB data
- ADR 0002: Storage Strategy

---

## 📦 Data Contract

### Message Schema (v1)

```json
{
  "timestamp": "2025-10-19T12:34:56.123Z",       // ISO 8601 UTC, message generated
  "vehicle_id": "veh-00123",                      // Unique vehicle identifier
  "can_id": "0x1F0",                              // CAN message ID (hex)
  "payload": {                                    // Decoded CAN signals
    "battery_soc": 85.5,                          // State of Charge (%)
    "battery_voltage": 400.2,                     // Pack voltage (V)
    "battery_current": -15.3,                     // Discharge current (A)
    "cell_voltage_min": 3.45,                     // Min cell voltage (V)
    "cell_voltage_max": 3.67,                     // Max cell voltage (V)
    "cell_temp_min": 28.5,                        // Min cell temp (°C)
    "cell_temp_max": 31.2                         // Max cell temp (°C)
  },
  "ingest_received_at": "2025-10-19T12:34:56.200Z"  // Server-side timestamp
}
```

**Design Notes**:
- `timestamp`: Client-side, may have clock skew
- `ingest_received_at`: Server-side, authoritative for ordering
- `payload`: Flat structure for MVP (nested later)
- All numeric values use standard units (no custom encoding)

---

## 🔧 Technical Implementation

### Batching Strategy

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| **Batch Size** | 100 messages | Balance latency vs throughput |
| **Batch Timeout** | 2 seconds | Max wait for batch to fill |
| **File Rotation** | 5 MB | Keep files manageable for S3 upload |
| **Long Polling** | 20 seconds | Reduce SQS API calls (cost) |
| **Visibility Timeout** | 30 seconds | Allow processing before re-queue |

**Processing Flow**:
1. Consumer polls SQS (up to 100 msgs, 20s long poll)
2. If messages received OR 2s timeout → flush batch
3. Write JSONL to time-partitioned path
4. Delete messages from SQS
5. Log latency metrics

### Time Partitioning

**Path Structure**:
```
data/raw/
  └── year=2025/
      └── month=10/
          └── day=19/
              └── hour=14/
                  ├── batch-1729344896123.jsonl
                  ├── batch-1729344898456.jsonl
                  └── ...
```

**Benefits**:
- **Efficient queries** by time range (Athena/Presto later)
- **Easy archival** (delete old partitions)
- **S3 lifecycle** policies apply per partition
- **Parallel processing** (Spark/Dask can process partitions independently)

### Latency Tracking

**Measured Latencies**:
1. **Ingest Latency**: `ingest_received_at - timestamp`
2. **Queue Latency**: Time in SQS (via message attributes)
3. **Processing Latency**: Poll → Write complete
4. **End-to-End Latency**: `timestamp` → JSONL write

**Metrics Logged** (per batch):
- P50, P95, P99 percentiles
- Min, Max values
- Batch size
- Processing timestamp

**Example Log**:
```
2025-10-19 14:30:00 INFO Batch processed: size=100, 
  e2e_latency_p95=3.2s, queue_latency_p95=1.1s, processing_latency=0.8s
```

---

## 📁 Project Structure

```
projects/can_data_platform/
├── src/
│   ├── __init__.py
│   ├── generator/                    # Battery telemetry simulator
│   │   ├── __init__.py
│   │   ├── battery_model.py          # Physics-based BMS simulation
│   │   ├── simulator.py              # Main event generator
│   │   └── dbc_signals.py            # BMW i3 DBC signal definitions
│   │
│   ├── receiver/                     # FastAPI ingestion service
│   │   ├── __init__.py
│   │   ├── app.py                    # FastAPI application
│   │   ├── models.py                 # Pydantic request/response models
│   │   └── auth.py                   # API key authentication
│   │
│   ├── consumer/                     # SQS batch consumer
│   │   ├── __init__.py
│   │   ├── batch_consumer.py         # Main consumer loop
│   │   ├── storage.py                # JSONL file writer
│   │   └── metrics.py                # Latency tracking
│   │
│   └── aggregator/                   # Data aggregation
│       ├── __init__.py
│       └── hourly_stats.py           # Hourly aggregation script
│
├── scripts/                          # Utility scripts
│   ├── setup_sqs.py                  # Create SQS queue
│   └── load_test.py                  # Generate test load
│
├── data/                             # Local data storage
│   ├── raw/                          # JSONL batches (time-partitioned)
│   └── aggregated/                   # Aggregation outputs
│
├── docs/                             # Project documentation
│   ├── architecture.md               # System design details
│   ├── api-spec.yaml                 # OpenAPI specification
│   └── deployment.md                 # Deployment guide
│
├── tests/                            # Unit & integration tests
│   ├── unit/
│   │   ├── test_battery_model.py
│   │   ├── test_receiver.py
│   │   └── test_consumer.py
│   └── integration/
│       └── test_end_to_end.py
│
├── README.md                         # This file
└── requirements.txt                  # Python dependencies
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- AWS account (Free Tier sufficient)
- AWS CLI configured (`aws configure`)
- (Optional) LocalStack for local AWS emulation

### Installation

1. **Navigate to project directory**
   ```bash
   cd projects/can_data_platform
   ```

2. **Install dependencies**
   ```bash
   pip install -r ../../requirements.txt
   pip install -r ../../requirements-test.txt
   ```

3. **Set up environment variables**
   ```bash
   # Create .env file
   cat > .env << EOF
   AWS_ACCESS_KEY_ID=your_access_key
   AWS_SECRET_ACCESS_KEY=your_secret_key
   AWS_DEFAULT_REGION=us-east-1
   API_KEY=your_secret_api_key_here
   SQS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/123456789012/telemetry-queue
   LOG_LEVEL=INFO
   EOF
   ```

4. **Create SQS queue**
   ```bash
   python scripts/setup_sqs.py
   # Copy the queue URL to .env
   ```

5. **Run tests**
   ```bash
   pytest ../../tests/
   ```

### Running the System

**Terminal 1: Start FastAPI receiver**
```bash
uvicorn src.receiver.app:app --reload --port 8000
```

**Terminal 2: Start batch consumer**
```bash
python src/consumer/batch_consumer.py
```

**Terminal 3: Run battery simulator**
```bash
python src/generator/simulator.py --vehicles 10 --duration 60
```

**Terminal 4: Monitor queue**
```bash
watch -n 5 'aws sqs get-queue-attributes --queue-url $SQS_QUEUE_URL --attribute-names ApproximateNumberOfMessages'
```

**Access API docs**: http://localhost:8000/docs

---

## 🧪 Testing

### Unit Tests

```bash
# Run all tests
pytest ../../tests/

# Run with coverage
pytest ../../tests/ --cov=src --cov-report=html

# Run specific test file
pytest ../../tests/unit/test_battery_model.py -v

# Run tests matching pattern
pytest ../../tests/ -k "battery" -v
```

### Integration Tests

```bash
# End-to-end pipeline test
pytest ../../tests/integration/test_end_to_end.py -v

# Use LocalStack for AWS services
LOCALSTACK=1 pytest ../../tests/integration/ -v
```

### Load Testing

```bash
# Generate 10,000 messages
python scripts/load_test.py --messages 10000 --rate 50

# Monitor latency during load
tail -f logs/consumer.log | grep "latency_p95"
```

---

## 📊 Monitoring & Metrics

### Key Metrics

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| **P95 End-to-End Latency** | < 5s | TBD | 🔄 Measuring |
| **Throughput** | > 100 msg/s | TBD | 🔄 Measuring |
| **Error Rate** | < 0.1% | 0% | ✅ Passing |
| **Test Coverage** | ≥ 95% | 96% | ✅ Passing |
| **Queue Depth** | < 1000 | 0 | ✅ Healthy |

### Logging

**Log Levels**:
- `DEBUG`: Detailed async operations, message contents
- `INFO`: Batch processing, metrics, queue status
- `WARNING`: Retries, near-threshold conditions
- `ERROR`: Processing failures, AWS API errors

**Example Logs**:
```
2025-10-19 14:30:00 INFO [Consumer] Polling SQS queue (long poll 20s)...
2025-10-19 14:30:02 INFO [Consumer] Received 100 messages
2025-10-19 14:30:03 INFO [Storage] Writing batch: data/raw/year=2025/month=10/day=19/hour=14/batch-1729344903.jsonl
2025-10-19 14:30:04 INFO [Metrics] Batch latency - P50: 2.1s, P95: 3.2s, P99: 4.1s
2025-10-19 14:30:04 INFO [Consumer] Deleted 100 messages from SQS
```

---

## 🏆 Success Criteria

### MVP Complete When:
- [x] Battery simulator generates realistic telemetry with module variance
- [x] FastAPI receiver accepts and validates messages
- [ ] SQS queue buffers messages with configurable retention
- [ ] Batch consumer writes time-partitioned JSONL files
- [ ] Latency tracking logs P50/P95/P99 metrics
- [ ] Hourly aggregation produces count per vehicle
- [ ] Integration test validates 1,000+ messages through pipeline
- [ ] ADR 0001 status changed to "Accepted"

---

## 🔄 Evolution Path

### Upgrade Triggers (When to Revisit Decisions)

| Condition | Trigger | Action |
|-----------|---------|--------|
| **Throughput** | Sustained > 5,000 msg/s | Consider Kinesis Data Streams |
| **Duplicate Rate** | > 0.5% | Switch to SQS FIFO or Kinesis |
| **Backlog Age** | Queue age > 60s | Add more consumer instances |
| **Latency** | P95 > 5s sustained | Optimize batch size/timeout |
| **Cost** | Monthly AWS bill > $50 | Review S3 lifecycle, SQS usage |
| **Query Performance** | Aggregation > 10min | Switch to Parquet, add Athena |

### Week 2: S3 Integration
- Upload JSONL batches to S3 after local write
- Configure lifecycle policies (Standard → IA → Glacier)
- Update aggregator to read from S3
- Add LocalStack integration tests
- Document ADR 0002: Storage Strategy

### Week 3: Documentation & Demo
- Polished README with architecture diagrams
- 5-minute demo video (screen recording + narration)
- Interview Q&A document with trade-off discussions
- Performance metrics summary dashboard
- Architecture decision records finalized

---

## 📚 Interview Talking Points

### System Design Questions

**Q: "Why SQS over Kinesis or Kafka?"**

A: "For this MVP use case:
- **SQS Standard** provides simplicity, low operational overhead, pay-per-use pricing
- **No ordering required** for analytics aggregation (can dedupe downstream)
- **Cost**: ~$0.40/million requests vs Kinesis $0.015/hour/shard (always running)
- **Upgrade trigger**: If duplicate rate >0.5% or need real-time streaming, migrate to Kinesis
- **Documented in ADR 0001** with clear decision rationale and measurable evolution criteria"

**Q: "How would you scale to 50,000 messages/second?"**

A: "Evolution path:
1. **Current (100 msg/s)**: Single SQS consumer, batch processing
2. **1,000 msg/s**: Add consumer instances (horizontal scaling), SQS auto-scales
3. **10,000 msg/s**: Switch to Kinesis Data Streams (multiple shards), parallel consumers
4. **50,000 msg/s**: Kinesis with auto-scaling shards, Kinesis Data Firehose → S3/Redshift
5. **Bottlenecks**: Network I/O (use ECS/EKS for auto-scaling), S3 throughput (partition keys)"

**Q: "Explain your batching strategy."**

A: "**Dual trigger batching**:
- Flush on **100 messages** (throughput optimization) OR **2-second timeout** (latency guarantee)
- Trade-off: Larger batches = fewer S3 writes (cost) but higher latency
- **P95 target <5s** drives 2s timeout choice
- **File rotation at 5MB** prevents single-file S3 upload issues
- Measured via latency tracking (P50/P95/P99 logged per batch)"

---

## 🎓 Learning Objectives

### Technical Skills Demonstrated
- [x] Async Python (FastAPI, asyncio, aiohttp)
- [x] AWS SQS integration (boto3, long polling, message deletion)
- [ ] Batch processing patterns (time-based + count-based triggers)
- [ ] Data engineering (time partitioning, JSONL, aggregation)
- [x] Unit testing (pytest, mocking, fixtures)
- [ ] Integration testing (LocalStack, end-to-end validation)
- [x] CI/CD quality gates (flake8, pylint, coverage enforcement)
- [x] Architecture documentation (ADRs, system diagrams)

### DevOps Practices
- [x] Infrastructure as Code (scripts for SQS setup)
- [x] Observability (logging, metrics, latency tracking)
- [x] Cost optimization (S3 lifecycle, SQS long polling)
- [x] Security (API key auth, IAM least privilege)
- [x] Version control (Git, feature branches, PR workflow)
- [x] Issue-driven development (GitHub Projects, milestones)

---

## 🛠️ Troubleshooting

### Common Issues

**Issue: "SQS messages not being deleted"**
```bash
# Check consumer logs for errors
tail -f logs/consumer.log

# Verify visibility timeout is sufficient
aws sqs get-queue-attributes --queue-url $SQS_QUEUE_URL --attribute-names VisibilityTimeout
```

**Issue: "Latency exceeds 5 seconds"**
```bash
# Check queue depth (backlog?)
aws sqs get-queue-attributes --queue-url $SQS_QUEUE_URL --attribute-names ApproximateNumberOfMessages

# Reduce batch size or timeout
# Edit consumer config: BATCH_SIZE=50, BATCH_TIMEOUT=1
```

**Issue: "Test coverage below 95%"**
```bash
# Generate detailed coverage report
pytest --cov=src --cov-report=html
open htmlcov/index.html

# Focus on uncovered lines
pytest --cov=src --cov-report=term-missing
```

---

## 📖 Additional Resources

- **ADR 0001**: [SQS Transport Decision](../../docs/adr/0001-ingestion-transport.md)
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **boto3 SQS**: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sqs.html
- **pytest**: https://docs.pytest.org/
- **LocalStack**: https://docs.localstack.cloud/

---

## 📝 Next Actions (Current Sprint)

**P01-Core-Pipeline-MVP** (Due: Oct 26, 2025):
1. [ ] Design and document data flow architecture (Issue #68)
2. [ ] Set up AWS SQS queue in dev environment (Issue #69)
3. [ ] Implement SQS publisher in event generator (Issue #70)
4. [ ] Build SQS batch consumer with JSONL output (Issue #71)
5. [ ] Add end-to-end latency tracking (Issue #72)
6. [ ] Build hourly aggregation script (Issue #73)
7. [ ] Create end-to-end integration test (Issue #74)
8. [ ] Accept ADR 0001 - SQS Transport Decision (Issue #75)

---

**Last Updated**: October 19, 2025  
**Status**: Active Development - Week 1 MVP  
**Next Milestone**: P01-Core-Pipeline-MVP (Due: Oct 26)
