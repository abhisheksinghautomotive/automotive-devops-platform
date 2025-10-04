# ADR 0001 – Ingestion Transport: SQS Queue for MVP

- Status: Proposed
- Date: 2025-10-04

## Context
We need a low-cost, simple, reliable way to buffer bursts of vehicle telemetry between the ingestion API and downstream storage/processing. Expected early load: simulated up to 50,000 msgs/sec scenario (design target), but initial real tests will be much lower. We prioritize simplicity, free-tier friendliness, and fast learning over perfect ordering or sub-second streaming analytics.

## Decision
Use AWS SQS Standard Queue as the ingestion buffer for the MVP.

## Options Considered
1. SQS Standard – Simple, low cost, at-least-once delivery, easy SDK integration.
2. Amazon Kinesis Data Streams – Scales well, ordering shards, higher complexity & baseline cost.
3. Managed Kafka (MSK) – Strong streaming semantics, ordering/consumer groups, operational + cost overhead.
4. Direct-to-S3 (no queue) – Simplest path but no burst smoothing, risk of write amplification & backpressure.

## Rationale
- Cost: SQS per-request pricing + free tier; no shard provisioning.
- Simplicity: Minimal configuration, quick to prototype; supports focus on core learning.
- Reliability: Built-in durability & retry semantics; natural decoupling.
- Evolvability: Easy to swap ingest publisher to Kinesis/MSK later when real-time processing window tightens.

## Trade-offs / Limitations
- No strict ordering guarantees (acceptable for MVP metrics).
- Approximate once delivery → possible duplicates (mitigation later via idempotency key or hash cache).
- Not ideal for low-latency sub-second stream transformations (acceptable because MVP uses batch writes).

## Consequences
Positive:
- Fast developer feedback loop.
- Low operational overhead – no server maintenance.
- Encourages thinking in decoupled producer/consumer pattern early.

Negative:
- Extra code for consumer batching vs direct stream transformation.
- Potential duplicates require future handling.
- Scaling to extremely high sustained throughput may require redesign.

## Mitigations
- Add message `ingest_id` (UUID) in future for dedupe.
- Introduce dead-letter emulation log for failed batches before managed DLQ usage.
- Document trigger conditions for upgrade.

## Metrics / Triggers to Revisit
| Trigger | Threshold | Action |
|---------|-----------|--------|
| Sustained msgs/sec | > 25k real (not simulated) | Evaluate Kinesis shard cost | 
| Duplicate rate | > 0.5% | Implement idempotency cache |
| Batch latency | > Target (5s) | Tune batch size / concurrency |
| Consumer backlog age | > 60s | Horizontal scale consumer or switch platform |

## Future Evolution Path
SQS → (Need ordering / lower-latency) → Kinesis (partition by vehicle_id) → (Complex multi-team analytics) → Kafka/MSK with schema registry.

## Status Rationale
Proposed until MVP ingest + first batch file is produced; then mark Accepted.

## Notes
Simplicity now accelerates learning and interview story creation (“We intentionally began with SQS to minimize cost and complexity; we defined upgrade triggers backed by metrics.”)
