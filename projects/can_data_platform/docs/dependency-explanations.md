# Dependency Explanations

| Package   | Version    | Purpose                                              | Optional? | Removal Impact          |
|-----------|------------|------------------------------------------------------|-----------|------------------------|
| fastapi   | ^0.110.0   | Runs backend simulation server (event receipt).      | No        | No event server/API    |
| uvicorn   | ^0.23.2    | ASGI server to run FastAPI app locally.              | No        | API server won't run   |
| requests  | ^2.31.0    | Sends HTTP requests to API server (from sender).     | No        | Sender cannot POST     |
| argparse  | stdlib     | Allows CLI arguments for scripts (event count, etc). | Yes       | Only hardcoded params  |
| random    | stdlib     | Generates random numbers for simulation.             | No        | Simulation not possible|
| json      | stdlib     | Reads/writes JSON data, sample event files.          | No        | Data I/O broken        |
| logging   | stdlib     | Saves workflow logs for sender/receiver/scripts.     | Yes       | Lose event/provenance  |

---

## Flagged/Unused Dependencies
- None in requirements.txt if only above are present.
- If extra/unusual packages are present (e.g. pandas, numpy, flask): flag and note if not currently used.

---

## Reflection

Every dependency included powers MVP simulation and dataflow, with only minimal helpers for CLI, I/O, and logging. Removing any non-stdlib package (fastapi, uvicorn, requests) would break a major component of the data pipeline. No suspicious or unused dependencies detected; setup is audit-ready and understandable for engineers and reviewers.

---

Time spent: **10 min**
Blocked days: **0**
