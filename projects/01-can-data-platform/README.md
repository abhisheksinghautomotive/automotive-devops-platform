# Project 01 – Telemetry Ingestion MVP (Lean Summary)

Focus: Ship a minimal, explainable ingestion + batching pipeline and capture upgrade triggers—not build a platform prematurely.

## MVP Goal
Simulated telemetry → FastAPI ingest → SQS buffer → batch consumer → JSONL files → trivial aggregate (count per vehicle) with latency logging.

Success Criteria (Initial):
* Functional: ≥10k synthetic messages accepted & persisted (JSONL) with no intentional loss.
* Latency: P95 ingest→persist < 5s.
* Clarity: You can whiteboard and justify every box + arrow.

## Scope Snapshot
Included: HTTP ingest, API key check, SQS standard, batch write JSONL, hourly aggregate script, basic latency logging.
Deferred: mTLS, Kafka/Kinesis, Parquet, dashboards, streaming analytics, fine-grained IAM, real DLQ infra.

## Data Contract (Draft v1)
```json
{
  "timestamp": "2025-10-04T12:34:56.123Z",
  "vehicle_id": "veh-00123",
  "can_id": "0x1F0",
  "payload": { "engine_rpm": 2150 },
  "ingest_received_at": "2025-10-04T12:34:56.200Z"
}
```
Notes: Keep payload tiny early (1–3 signals). `ingest_received_at` added server-side.

## Batching Rules (Initial)
* Poll up to 100 msgs OR 2s timeout.
* Flush to path: `raw/year=YYYY/month=MM/day=DD/hour=HH/part-<uuid>.jsonl`.
* Rotate if file > ~5MB.

## Minimal Reliability Tactics
| Risk | MVP Handling | Upgrade Trigger |
|------|--------------|-----------------|
| Burst spike | Queue absorption | Sustained backlog age >60s |
| Failed write | Retry once then log | Error rate trend > threshold |
| Duplicates | Ignore | Duplicate rate >0.5% |
| Consumer crash | Manual restart | Need auto-recovery (containerize) |

## Cost Levers (Defaults)
SQS standard (no shard mgmt) | JSONL (simple) | Batch size=100 | Retain raw 7d (placeholder) | Hourly aggregate.

## Observability (Seed)
Log: batch size, p50/p95 latency samples, message counts / minute. Queue depth manual for now.

## Security
Single API key env var; reject missing/invalid. HTTPS deferred (local learning focus).

## Build Order (Strict)
1. FastAPI endpoint + API key.
2. Publish to SQS.
3. Batch consumer flush JSONL.
4. Latency logging per batch.
5. Aggregate counts per vehicle/hour.
6. Produce first dataset → Accept ADR 0001.

## Definition of Done (MVP)
* ≥1 JSONL batch file (>1000 msgs) committed or demonstrable.
* Logged latency distribution (at least p50/p95 sample lines).
* ADR 0001 status flipped to Accepted.
* README + schema updated to reflect reality.

## Post-MVP Candidates (Parking Lot)
Parquet conversion | Simple anomaly rule | Metric export | Dedupe experiment | Sliding window ring buffer.

## Immediate Next Actions (Rolling 3)
1. Finalize schema in code + doc.
2. Implement & test batch consumer (JSONL + latency metrics).
3. Generate first hourly aggregate output.

Stay narrow. Anything outside these steps requires an issue + justification.
