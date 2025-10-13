# Progress Tracking & Focus Guide

Purpose: A clear, lightweight system to track progress daily and prevent context switching. This mirrors professional workflows while staying lean and low-cost.

Status: Living document (keep concise and practical)
Date: 2025-10-13

---

## 1) Core Principles
- Issue-first: No work without an open GitHub Issue. Every commit/PR links to it.
- One thing at a time: Exactly one active feature branch unless the current task is blocked and the block reason is logged.
- Concept → Implementation → Refinement → Interview: Close concept before starting code. Each issue has one phase.
- Pseudocode before code: Any non-trivial logic gets a short pseudocode artifact first.
- Small, visible steps: Each issue produces one concrete artifact (doc, table, pseudocode, code change, or metric snapshot).

---

## 2) Daily Flow (Checklist)
1. Choose your ONE active issue for today (phase:concept or phase:implementation).
2. Write/confirm Exit Criteria in the issue body (≤4 bullets, concrete, testable).
3. Do focused work in ≤2-hour blocks; pause only to note blockers or questions.
4. Commit with the issue ID in message; keep changes scoped to the issue.
5. Update `progress-tracking/daily-log.md` with a one-line reflection.
6. If you finish: close the issue with reflection; otherwise, leave a short next-step note.

---

## 3) Weekly Review (15–20 min)
- Close or re-scope any concept idle ≥7 days.
- Pick the next 1–2 concept issues only.
- Convert accepted suggestions into issues; no silent backlog.
- Add a weekly summary line in the daily log.

Optional commands to prep:
```zsh
# Past week highlights
git log --since="1 week ago" --oneline --grep="feat\|docs\|refactor" --author="$(git config user.email)"
```

---

## 4) Issue Hygiene (Strict)
- Exactly one phase label: `phase:concept` | `phase:implementation` | `phase:refinement` | `phase:interview`.
- WIP limit: ≤2 open concept issues in the same domain; otherwise defer.
- Use this minimal template in the issue body:
```
Goal:
Artifact:
Why Now:
Steps:
  - [ ] ...
Exit Criteria:
Reflection: <fill before close>
```

Definition of Done per phase:
- concept: Artifact + assumptions listed + reflection added
- implementation: Code runs locally + basic verification note + linked concept closed
- refinement: Before/after (or rationale) + improvement backlog updated
- interview: Story outline + Q&A bullets or one rehearsal note

---

## 5) Branching & Commits
- Branch names: `feature/<issue>-<slug>` (e.g., `feature/7-bmw-battery-dbc-inspect`).
- One active feature branch at a time; delete after merge.
- Commit format:
```
<type>(<issue>-<scope>): <description>
# Example
docs(7-bmw-battery-dbc-inspect): populate DBC survey with module cell voltages
```
- Merge policy: squash (or consistent no-ff); keep history linear.

---

## 6) Stick-to-Task Rules (Anti-Diversion)
- Focus Funnel: Milestone → Phase → Domain → Issue → Artifact. Do not skip levels.
- New idea mid-task? Add a comment to a Parking Lot issue; do not switch.
- Blocked >24h? Add `status:blocked` with reason; only then start a second branch.
- No coding without a concept artifact for new areas (simulation/pipeline/infra).
- No parallel concept issues in the same domain beyond 2 (WIP limit).

Acceptance Checklist for starting a task now (all YES):
- Relevant to current milestone?
- Sequencing ok (prereqs closed)?
- Clear goal + artifact + exit criteria (≤4 bullets)?
- Right-sized (size:s or size:m)?
- Unique (not overlapping an open issue)?

If any NO → Defer or refine.

---

## 7) Daily Log (Where/How)
- Location: `progress-tracking/daily-log.md`
- One-line per day is enough; add more if it helps.

Entry template:
```
## 2025-10-13
- Focus Issue: #7 Parse BMW battery DBC (concept)
- Artifact: battery-dbc-survey.md updated (signals + notes)
- Result: finalized cell-voltage MVP subset; created sample JSONL
- Blockers: none
- Next: value evolution model (draft rules)
- Reflection: starting with clear cell voltages kept scope tight and cost near-zero
```

---

## 8) Minimal Metrics to Track
- Time spent (optional): 25–120 min blocks.
- Artifacts produced: file paths.
- New terms/concepts learned: 1–2 bullets.
- Blockers + date.
- Decision snapshot: “Keep or change direction?”

---

## Issue Metrics Template in GitHub
Goal:
Artifact:
Time Spent: <fill before close>
Blocked Days: <fill if needed>
Reflection: <fill before close>


## 9) Examples (Current Work)
- Issue: #7 BMW battery DBC inspection → `battery-dbc-survey.md` (concept) → complete.
- Signals selected (MVP): Cell_1_Voltage_mV, Cell_4_Voltage_mV + derived avg/min/max.
- Sample data: `docs/samples/sample-events-mvp.jsonl` created.
- Next issue: value evolution model (concept) → then simulator integration (implementation).

Keep it lean: if a step doesn’t move the active issue to Done, it waits.
