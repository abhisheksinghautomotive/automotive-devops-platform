# Project 01 – Cloud-Native Telemetry Platform (MVP Architecture Outline)

> Focus: Learn fundamentals with a minimal, cost-aware pipeline you can explain clearly.

## 1. MVP Goal (Simple Statement)
Ingest simulated vehicle telemetry, buffer it safely, batch-store it cheaply, and produce a basic aggregate metric—while capturing latency and cost awareness.

Success (initial):
- Functional: Accept 10k synthetic messages without loss into storage.
- Metric: End-to-end latency (ingest → persisted) under 5 seconds (non-real-time tolerance for MVP).
- Learning: You can whiteboard every component and justify each choice.

## 2. MVP Scope (Included vs Deferred)
| Included Now | Deferred (Later Phase) | Why Deferred |
|--------------|------------------------|--------------|
| HTTP ingest endpoint | Edge auth hardening (mTLS) | Start simple; avoid cert complexity |
| API key header check | Fine-grained IAM per signal | Overhead not needed yet |
| SQS standard queue | Kafka/Kinesis | Higher cost / complexity |
| Batch consumer (Python) | Real-time stream processing (Flink) | Not needed for first learning |
| Raw JSONL to S3 (partitioned) | Time-series DB (Timestream) | Adds cost + config |
| Simple aggregation script | Real dashboard (Grafana) | Need data first |
| Basic latency logging | Full observability stack | Avoid tool sprawl |
| Retry + DLQ concept (emulated) | Managed DLQ metrics | Keep mental model small |

## 3. Component Diagram (Text Form)
```
Vehicle Simulator -> HTTP Ingest (FastAPI) -> SQS Queue -> Batch Consumer -> S3 (raw/...) -> Aggregator Script -> Aggregates (S3) -> (Future Dashboard)
```

## 4. Data Contract (Draft v1)
```json
{
  "timestamp": "2025-10-04T12:34:56.123Z",
  "vehicle_id": "veh-00123",
  "can_id": "0x1F0",
  "payload": { "engine_rpm": 2150, "brake_status": false },
  "ingest_received_at": "2025-10-04T12:34:56.200Z"
}
```
Notes:
- `ingest_received_at` added server-side.
- Keep payload small; only 1–3 signals per message at first.

## 5. Batching Strategy
- Consumer polls up to N messages (start N=100) or timeout (e.g. 2s).
- Writes one `.jsonl` file: `raw/year=YYYY/month=MM/day=DD/hour=HH/part-<uuid>.jsonl`.
- Rotate file when size > ~5MB or after max batch interval.

## 6. Sliding Window (Future Prep)
Not implemented now. Later: maintain last 60s per vehicle for real-time stats; ring buffer with fixed-length array of (timestamp,value) pairs.

## 7. Reliability Tactics (Minimal)
| Concern | MVP Tactic | Upgrade Path |
|---------|------------|--------------|
| Burst spike | Queue buffers | Autoscaling consumer(s) |
| Failed batch write | Retry whole batch once, then log | DLQ with replayer |
| Duplicate messages | (Ignore) | Hash-based dedupe cache |
| Lost consumer | Manual restart | Supervisor / container orchestration |

## 8. Cost Levers
| Lever | Low-Cost Default | Future Optimization |
|-------|------------------|---------------------|
| Queue choice | SQS standard | Kinesis / MSK when scale proves |
| Storage format | JSONL | Parquet (compression + efficient scan) |
| Batch size | 100 | Adaptive based on latency budget |
| Retention raw | 7 days | Tier to Glacier / delete older |
| Aggregates | Hourly script | Streaming incremental view |

## 9. Observability (MVP Set)
| Metric | How Captured |
|--------|--------------|
| Ingest rate | Log count per minute | CloudWatch custom metric later |
| End-to-end latency | `now - timestamp` at write | Export sample distribution |
| Queue depth (manual) | AWS console / CLI | Automated alert later |

Add simple logging format:
```
LEVEL time=... event=write_batch size=N latency_p50=...ms latency_p95=...ms
```

## 10. Security (Minimal)
- Single API key in environment variable.
- Reject if header missing or mismatched.
- HTTPS enforced via cloud fronting (future) or local dev just HTTP for learning.

## 11. Risks & Open Questions
| Area | Question | Decision Timeline |
|------|----------|-------------------|
| Auth | When to rotate key? | After first stable ingest |
| Aggregation | Minute vs hour first? | Decide after first dataset |
| Schema | Add VIN or region? | When doing analytics |
| Format | Switch to Parquet? | After > 1GB accumulated |

## 12. Step-by-Step Build Order
1. Create Python virtual env + basic FastAPI ingest endpoint.
2. Add API key check.
3. Integrate SQS send (batching not needed at producer side).
4. Write consumer: poll, accumulate, flush to S3 JSONL.
5. Log per-batch latency stats.
6. Write simple aggregation script (count messages per vehicle per hour).
7. Produce first metrics summary file.
8. Review + create ADR 0001.

## 13. Done Definition (MVP)
- Code runs locally with mocked AWS (e.g. `localstack`) OR minimal real AWS usage within free tier.
- At least one `.jsonl` file produced with >1000 messages.
- Latency samples logged.
- Architecture + ADR committed.

## 14. Next (Post-MVP) Candidates
- Parquet conversion job.
- Basic anomaly rule (e.g., RPM > threshold count).
- CloudWatch metrics & alert.
- Dedupe prototype.

---
*Keep this file living; update sections as decisions evolve.*
