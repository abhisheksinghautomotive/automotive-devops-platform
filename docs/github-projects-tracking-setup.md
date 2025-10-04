# Project Tracking Setup - GitHub Projects v2

## 🎯 Recommended Tool: GitHub Projects v2

**Why GitHub Projects v2:**
- ✅ **Native Integration**: Seamless connection with repository, issues, and PRs
- ✅ **Learning Analytics**: Custom fields for tracking skill progression
- ✅ **Professional Showcase**: Visible to potential employers on GitHub profile
- ✅ **Flexible Views**: Kanban, table, roadmap views for different perspectives
- ✅ **Automation**: GitHub Actions integration for automated progress tracking

## 📊 Project Setup Structure

### ⚡ Starter Mode (Weeks 1–2)
Use only what builds habit—avoid over-configuring.
| Element | Use Now | Defer | Rationale |
|---------|---------|-------|-----------|
| Columns | Backlog, In Progress, Review, Done | Interview Ready column | Keep board lean |
| Fields | Project Phase, Priority | Skill Level, Interview Readiness, Business Impact, Hours | Reduce friction |
| Labels | `project-01-telemetry`, `status-in-progress`, `status-completed` | Skill + future project labels | Start focused |
| Metrics | Issues closed/week, Refined answers count, Avg batch latency | Cost per 1K msgs (later) | Simplicity first |
| Automation | None | Progress workflow | Build manual rhythm first |
| Views | Kanban only | Roadmap, Interview dashboard, Learning table | Avoid empty views |

# Minimal Project Tracking (GitHub Projects)

Goal: Track progress without overhead while building Project 01.

## 1. Board Setup (Takes 2 Minutes)
Columns: Backlog | In Progress | Review | Done

## 2. Create 5 Micro Issues
Suggested:
1. Create FastAPI skeleton
2. Add API key validation
3. Simulate vehicle messages script
4. Batch list in memory & log count
5. Update project README with flow

Move one issue at a time. No multitasking.

## 3. Daily Log
File: `progress-tracking/daily-log.md`
Format:
```
YYYY-MM-DD | Did: <task> | Learned: <concept> | Next: <focus>
```

## 4. Minimal Fields / Labels
- Field: Project Phase (Planning → Development → Review)
- Label (optional): `project-01-telemetry`
- Status is shown by column; no extra labels needed.

## 5. Only 2 Metrics (Weekly)
| Metric | How |
|--------|-----|
| Issues closed | Count Done column |
| Refined answers | Count updated answers (V2+) in question bank |

Log them each weekend in a short weekly note.

## 6. Upgrade Triggers (Don’t Add Before These)
| Unlock | Trigger |
|--------|---------|
| Add Skill Level field | 10 issues closed |
| Add Interview Readiness | First aggregation script done |
| Add Automation | 2 weekly summaries written |

## 7. Workflow Loop
Plan → Do → Log → Move card → Reflect (weekly)

## 8. Keep It Lean
Skip: hours tracking, business impact, dashboards, automation—for now.

## 9. Weekly Reflection (One Paragraph)
Format:
```
Week #: Built <X>. Learned <Y>. Struggled with <Z>. Next: <focus>.
```

## 10. Link Decisions
When a decision is made (e.g., SQS choice) link ADR file in issue comment for traceability.

---
Later (Optional) Advanced Mode lives in commit history; reintroduce when you are ready.
```
progress-tracking/daily-log.md
2025-10-04 | Focus: ingestion endpoint | Win: first 200 OK | Next: add SQS client
```

#### Connecting Issues to Code:
```bash
# Link commits to issues
git commit -m "feat(data-pipeline): Implement rate limiting algorithm

Closes #15: Implement token bucket rate limiting
- Add configurable rate limits per vehicle
- Handle burst traffic scenarios  
- Add monitoring metrics for rate limiting

Related to project-01-telemetry milestone"
```

#### PR Templates:
```markdown
## Project Learning Summary
**Project**: [Project name]
**Component**: [Component implemented]
**Learning Objectives Achieved**: 
- [ ] [Objective 1]
- [ ] [Objective 2]

## Technical Implementation
**Architecture Decisions**:
- [Decision 1 and rationale]
- [Decision 2 and rationale]

**Performance Results**:
- [Quantified improvements]
- [Benchmarking results]

## Interview Preparation
**System Design Story**:
- [How you'd explain this in an interview]

**Technical Depth Demonstration**:
- [Key technical concepts mastered]

**Business Impact**:
- [Quantified outcomes and improvements]

## Next Steps
- [ ] Update project documentation
- [ ] Prepare demo for interview scenarios
- [ ] Plan next learning phase
```

## 🎯 Success Metrics

### Learning Progress KPIs:
- **Project Completion Rate**: Target 100% within 12 weeks
- **Skill Progression**: Achieve "Advanced" level in core skills
- **Interview Readiness**: All projects "Interview Ready" by week 10
- **Time Management**: <20% variance between estimated and actual hours

### Portfolio Quality Indicators:
- **Technical Depth**: Can explain architecture decisions and trade-offs
- **Business Impact**: Have quantified results for all major implementations
- **Demonstration Ready**: Live demos prepared for all projects
- **Story Development**: Compelling technical and behavioral interview stories

## 🚀 Getting Started

### Initial Setup Steps (Starter Mode):
1. Create GitHub Project (Kanban only, Backlog/In Progress/Review/Done).
2. Add two custom fields: Project Phase, Priority.
3. Create 5 micro issues (e.g., "Create FastAPI skeleton", "Add API key check").
4. Start `daily-log.md` and log first entry after completing one issue.
5. Add ADR 0001 link to project README for traceability.
6. Defer automation & extra views until triggers met.

This comprehensive tracking system ensures you maintain momentum, track skill development, and prepare systematically for technical interviews while building an impressive DevOps platform portfolio.