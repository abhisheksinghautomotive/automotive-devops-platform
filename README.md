# Automotive DevOps Platform (Lean Mode)

Badges: In development | MIT License

Single-repo learning journey building a Software-Defined Vehicle (SDV) oriented DevOps platform through 6 progressively harder projects. Only Project 01 is active; everything else is explicitly deferred to protect focus.

## Current Focus
Project 01 – Minimal cloud-native telemetry ingestion (simulate → ingest → buffer → batch store → simple aggregate) with conscious trade‑offs you can explain.

## Why This Exists
Practice professional architecture & Git hygiene while producing interview‑ready stories about: ingestion design, cost vs complexity choices, evolution triggers, and disciplined process.

## Active Surface Area (Today)
```
projects/01-can-data-platform/   # Working project (MVP scope only)
docs/adr/                        # ADR 0001 (ingestion transport)
docs/git-branching-strategy.md   # Lean branching rules
progress-tracking/daily-log.md   # Reflection log
.github/instructions/ai-learning-guide.instructions.md
```

Everything else (K8s platform, full CI/CD, IaC scale-out, observability stack) is intentionally deferred and will re-enter only via approved issues.

## Lightweight Roadmap (Snapshot)
| ID | Project (Future) | Status |
|----|------------------|--------|
| 01 | Telemetry Ingestion MVP | In Progress |
| 02 | Containerized Test Framework | Deferred |
| 03 | Enterprise CI/CD | Deferred |
| 04 | Kubernetes Platform | Deferred |
| 05 | Infra as Code | Deferred |
| 06 | SDV Platform Rollup | Deferred |

## Process Guardrails
1. Issue first. No branch without a linked issue.
2. One feature branch at a time (unless blocked & documented).
3. Pseudocode / doc before code for new conceptual areas.
4. ADR for any foundational technical fork in the road.
5. Daily reflection logged (what moved, what is blocked, next action).

## Quick Start (Project 01)
```bash
git clone https://github.com/your-username/automotive-devops-platform.git
cd automotive-devops-platform
python -m venv .venv && source .venv/bin/activate
pip install -r projects/01-can-data-platform/requirements.txt  # if present
uvicorn projects.01-can-data-platform.app:app --reload  # placeholder path; adjust once module exists
```
If code module not yet implemented, start with documentation + ADR review:
```
open projects/01-can-data-platform/README.md
open docs/adr/0001-ingestion-transport.md
```

## Project 01 (MVP Contract)
Goal: Accept synthetic telemetry, buffer with SQS, batch flush to S3 (or local placeholder), compute a trivial aggregate (count per vehicle), and log latency distribution.

Included Now:
* FastAPI ingest endpoint (API key header)
* Publish to SQS (standard queue)
* Batch consumer -> JSONL files (time-partitioned path)
* Simple hourly aggregation script
* Basic latency logging

Deferred (On Purpose): mTLS, Kafka/Kinesis, Parquet, dashboards, streaming analytics, full observability, IAM fine‑grained policies.

## Key Decision (ADR 0001)
Ingestion buffer = SQS Standard (simplicity + cost). Upgrade triggers defined (throughput, duplicate rate, backlog age, latency).

## Next 3 Concrete Actions (Rolling)
1. Finalize minimal data schema + document in Project 01 README.
2. Implement batch consumer writing JSONL with latency logging.
3. Produce first aggregate file and mark ADR 0001 Accepted.

## Interview Angles (Seed)
* Trade-off: SQS vs Kinesis vs Kafka – cost, operational overhead, ordering.
* MVP latency vs engineering effort – why batch first.
* Evolution path & measurable upgrade triggers.

## Contributing (Solo Mode)
Use branch pattern: `feature/<issue>-<slug>`; squash merge; delete branch immediately. Experiments: `experiment/<spike>` (≤24h, summarize then delete).

## License
MIT (see LICENSE).

---
Stay lean. Anything not pushing Project 01 forward is noise.