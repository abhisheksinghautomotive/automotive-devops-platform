# Progress Tracking & Focus Guide

Purpose: A clear, lightweight system to track progress daily and prevent context switching. This mirrors professional workflows while staying lean and low-cost.

Status: Living document (keep concise and practical)
Date: 2025-10-13


## 1) Core Principles


## 2) Daily Flow (Checklist)
1. Choose your ONE active issue for today (phase:concept or phase:implementation).
2. Write/confirm Exit Criteria in the issue body (≤4 bullets, concrete, testable).
3. Do focused work in ≤2-hour blocks; pause only to note blockers or questions.
4. Commit with the issue ID in message; keep changes scoped to the issue.
5. Update `progress-tracking/daily-log.md` with a one-line reflection.
6. If you finish: close the issue with reflection; otherwise, leave a short next-step note.


## 3) Weekly Review (15–20 min)

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

```
