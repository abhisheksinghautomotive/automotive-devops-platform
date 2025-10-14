# Progress Tracking & Focus Guide

Purpose: A clear, lightweight system to track progress daily and prevent context switching. This mirrors professional workflows while staying lean and low-cost.

Status: Living document (keep concise and practical)
Date: 2025-10-13


## 1) Core Principles
- Issue-first: No work starts without an open GitHub Issue; every commit/PR links to it.
- One thing at a time: Exactly one active feature branch unless the current task is blocked and the block reason is logged.
- Phase flow: Concept → Implementation → Refinement → Interview. Close the concept issue before writing production code.
- Pseudocode before code: Any non-trivial logic (simulation, pipeline, infra) gets a short pseudocode artifact first.
- Small, visible steps: Each issue produces one concrete artifact and has ≤4 exit-criteria bullets.
- Cost-aware: Prefer local, zero-cost validation (docs/samples) over cloud resources until needed.
- Definition of Done: Use phase-specific DoD to decide when to close issues and move forward.


## 2) Daily Flow (Checklist)
1. Choose your ONE active issue for today (phase:concept or phase:implementation).
2. Write/confirm Exit Criteria in the issue body (≤4 bullets, concrete, testable).
3. Do focused work in ≤2-hour blocks; pause only to note blockers or questions.
4. Commit with the issue ID in message; keep changes scoped to the issue.
5. Update `progress-tracking/daily-log.md` with a one-line reflection.
6. If you finish: close the issue with reflection; otherwise, leave a short next-step note.


## 3) Weekly Review (15–20 min)

Checklist:
- Close or re-scope any concept idle ≥7 days
- Pick the next 1–2 concept issues only
- Convert accepted suggestions into issues; no silent backlog
- Add a weekly summary line in the daily log
- Add “What worked / What was blocked / What’s next” bullets for the week

Optional commands to prep:
```zsh
# Past week highlights
git log --since="1 week ago" --oneline --grep="feat\|docs\|refactor" --author="$(git config user.email)"
```


## 4) Issue Hygiene (Strict)
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


## 5) Branching & Commits
```
<type>(<issue>-<scope>): <description>
# Example
docs(7-bmw-battery-dbc-inspect): populate DBC survey with module cell voltages
```


## 6) Stick-to-Task Rules (Anti-Diversion)

Acceptance Checklist for starting a task now (all YES):

If any NO → Defer or refine.


## 7) Daily Log (Where/How)

Entry template:
```
## 2025-10-13
```


## 8) Minimal Metrics to Track
- Time Spent: Total focused time on the issue (e.g., 1h 30m). Fill in the issue on close.
- Blocked Days: Count and reason (e.g., 2 days waiting for X). Fill in the issue on close.
- Artifacts Produced: File paths and a one-liner (e.g., docs, schema, sample data).
- New Concepts Learned: 1–2 bullets to aid interview stories.
- Decision Snapshot: Keep/change direction notes (with rationale).
- Basic Implementation Metrics (when relevant): e.g., event count accepted, rough latency.

How to log
- Daily: Add a row in `progress-tracking/daily-log.md` with Date, Issue, Phase, Time Spent, Blocked, Reflection.
- On Close: Populate “Time Spent” and “Blocked Days” fields in the issue body template.


## Issue Metrics Template in GitHub
Goal:
Artifact:
Time Spent: fill before close
Blocked Days: fill if needed
Reflection: fill before close


## 9) Examples (Current Work)

Keep it lean: if a step doesn’t move the active issue to Done, it waits.

## Metrics: Time Spent and Blocked Days

- Add to every issue body (fill on close):
  - Time Spent: e.g., 3h 45m
  - Blocked Days: e.g., 2 days (waiting for X)
- Log daily in `progress-tracking/daily-log.md` with columns: Date, Issue, Phase, Time Spent, Blocked, Reflection

### Weekly Summary Template

Add one section per calendar week (e.g., 2025-W42):

```
## Weekly Summary (YYYY-Www)
- Total time spent: <sum>
- Total blocked days: <sum>
- Key learning: <one line>
```

## Milestones and Tags

- Create milestones in GitHub (Issues → Milestones) for major goals (e.g., Project 01 MVP)
- Reference milestones in issues; close when all issues complete
- Tag code for completed milestones:
  - Create annotated tag and push:
    - git tag -a v1-project-01-complete -m "Project 01 complete: Ingestion MVP works end-to-end"
    - git push origin v1-project-01-complete
- Reference tags/milestones in docs for easy navigation

---

## Quick Reference

| Feature                 | How To Do It                                      | Where                  |
|-------------------------|---------------------------------------------------|------------------------|
| Time Spent per Issue    | Add “Time Spent:” field in issue body/table       | Issues / Daily Log     |
| Blocked Days per Issue  | Add “Blocked Days:” field in issues/logs          | Issues / Daily Log     |
| Weekly Totals           | Summarize totals in weekly review                 | This guide (weekly sec)|
| GitHub Milestones       | Create via Issues → Milestones UI                 | GitHub UI              |
| Tag Completed Versions  | `git tag -a … && git push origin …`               | Local Git + GitHub     |

---

## End-of-MVP Retrospective (add after shipping MVP)

Create a short retrospective to crystallize learnings, tradeoffs, and business value.

Template:
```
## Retrospective: <Project/MVP Name>
Date: <yyyy-mm-dd>

What worked:
- 

What was blocked / slowed us:
- 

Key trade-offs made:
- 

Outcomes / business value:
- 

What we’ll change next time:
- 
```
```
