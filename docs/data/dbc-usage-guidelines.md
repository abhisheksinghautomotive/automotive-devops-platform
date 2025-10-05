# DBC Usage Guidelines (External CAN Database Files)

> Status: Initial draft for learning & simulation. These DBC files are treated as external, non-redistributed assets.

## 1. Purpose
We use selected CAN DBC (Database) files to drive more realistic battery & powertrain telemetry simulations (e.g. SOC, pack voltage, current, temperatures) instead of purely random values. This improves:
- Data realism (value ranges & relationships)
- Interview storytelling (demonstrating domain awareness)
- Future extensibility (raw vs decoded ingestion roadmap)

## 2. Source & Licensing Caution
- Upstream repository: `https://github.com/jamiejones85/DBC-files`
- As of retrieval, that repo does **not** include an explicit LICENSE file (404 when fetching `/LICENSE`).
- Without a license, default is effectively “All rights reserved.” You should NOT re-publish or vendor those files in a public repo without permission.

### What We Do Instead
| Approach | Decision | Rationale |
|----------|----------|-----------|
| Commit raw DBC files here | ❌ Avoid | Unknown license / potential infringement |
| Keep local copy under `data/raw/DBC-files-master/` | ✅ Yes | Local development only |
| Document retrieval steps | ✅ Yes | Reproducibility |
| Provide automated fetch script | ✅ (optional) | Convenience; still respects upstream |
| Git submodule | ⚠️ Only if license clarified | Submodules replicate content; still redistribution |

## 3. .gitignore Placement
The folder `data/raw/DBC-files-master/` is listed in `.gitignore` so local copies do not get committed. If you rename or reorganize, update `.gitignore` accordingly.

## 4. Retrieval Options
Pick one method.

### Option A: Manual Clone (One-Time)
```bash
mkdir -p data/raw
cd data/raw
git clone https://github.com/jamiejones85/DBC-files.git DBC-files-master
```

### Option B: Shallow Fetch (Lightweight)
```bash
mkdir -p data/raw/DBC-files-master
curl -L -o data/raw/DBC-files-master/BMW-PHEV-HV-Battery.dbc \
  https://raw.githubusercontent.com/jamiejones85/DBC-files/master/BMW-PHEV-HV-Battery.dbc
```
Repeat for any other `.dbc` you need.

### Option C: Helper Script (Not yet added)
Create `scripts/fetch_dbc_files.sh` (optional) with curl lines; mark executable. Because license is unclear, keep script minimal and *do not* mirror entire repo by default.

## 5. Why Not a Git Submodule (Yet)?
Submodules embed a pointer to another repository’s content. This still functions as redistribution if your repo is public and the upstream lacks an explicit permissive license. If the owner later adds MIT/GPL/etc., you can revisit adding a read-only submodule pinned to a specific commit hash.

## 6. Using DBC Files Programmatically
We will (optionally) use `cantools` to parse and inspect messages.

Add to `requirements.txt` ONLY after you intentionally adopt parsing:
```
cantools
```

> For now we do not auto-add this dependency—explicit learning step.

### Core Parsing Steps (Conceptual)
1. Load file: `db = cantools.database.load_file(path)`
2. Iterate messages: `for m in db.messages:`
3. For each message, inspect: `m.name`, `hex(m.frame_id)`, `len(m.signals)`
4. For target battery message(s), list signals with: name, start bit, length, factor, offset, choices.
5. (Later) Encode test values & decode round-trip to confirm correctness.

## 7. Sample Inspection Script (Copy When Ready)
`scripts/inspect_bmw_battery_dbc.py` (not created yet—paste when needed):
```python
#!/usr/bin/env python3
"""Inspect BMW HV battery DBC and print candidate battery-related messages."""
import os, sys
import cantools

PATH = "data/raw/DBC-files-master/BMW-PHEV-HV-Battery.dbc"

def main():
    if not os.path.isfile(PATH):
        print(f"DBC not found: {PATH}\nFetch it first (see docs/data/dbc-usage-guidelines.md)")
        sys.exit(1)
    db = cantools.database.load_file(PATH)
    print(f"Loaded {len(db.messages)} messages")
    # Filter heuristics: names containing battery related tokens
    tokens = {"BATT", "HV", "CELL", "PACK", "SOC"}
    candidates = []
    for msg in db.messages:
        upper_name = msg.name.upper()
        if any(tok in upper_name for tok in tokens):
            candidates.append(msg)
    print(f"Found {len(candidates)} candidate battery messages:\n")
    for msg in candidates[:10]:  # show first 10
        print(f"Message: {msg.name} id=0x{msg.frame_id:X} signals={len(msg.signals)}")
        for sig in msg.signals[:8]:  # limit per message
            print(f"  - {sig.name} (start:{sig.start} len:{sig.length} factor:{sig.scale} offset:{sig.offset})")
        print()
    print("(Truncated output; adjust limits as needed.)")

if __name__ == "__main__":
    main()
```

### You’ll Learn
- How to scan messages for naming conventions
- How scaling (factor) & offset turn raw bits into physical values
- How to shortlist core signals (SOC, voltage, current, temps)

## 8. Selecting Core Battery Signals
After inspection, record chosen signals in a doc table:
| Signal | Units | Factor | Offset | Bits | Notes |
|--------|-------|--------|--------|------|-------|

You’ll then define a simulation storyline (charge or discharge) using those ranges.

## 9. Simulation Strategy (Preview)
Simplest initial CHARGE scenario:
| Step | SOC% | Pack V | Current A (+ = charging) | Temp Avg C | Temp Max C |
|------|------|--------|--------------------------|------------|------------|
| 0 | 40.0 | 360.5 | 32.0 | 26.0 | 28.0 |
| 1 | 41.2 | 361.0 | 31.5 | 26.1 | 28.1 |
| ... | ... | ... | ... | ... | ... |
| 9 | 50.3 | 365.2 | 28.0 | 27.0 | 29.0 |

Later refinements: taper current near target SOC, introduce small noise, temperature thermal lag.

## 10. Raw vs Decoded Data (Roadmap)
| Mode | Pros | Cons |
|------|------|------|
| Decoded JSON only | Fast to integrate with current ingest API | Lose original bit-level fidelity |
| Raw CAN frame + decoded | Future-proof, re-decodable | Slightly more payload size & complexity |

Initial recommendation: start with decoded JSON; add raw frame later as a separate field.

## 11. Open Actions
- [ ] Run inspection script (after adding cantools)
- [ ] Shortlist target messages
- [ ] Populate signal table
- [ ] Draft 10-sample manual scenario
- [ ] Integrate into generator

## 12. FAQ
**Q: Why not automatically fetch on install?**  
Because license is unclear—forces deliberate user action.

**Q: Can we add the upstream repo as a submodule?**  
Not recommended until license clarity; submodule still republishes structure.

**Q: When to store raw frames?**  
Once ingestion stability + validation pipeline exists.

---
**Reminder:** Treat external DBC files as transient, local learning inputs until licensing is clarified or replaced with self-authored equivalents.
