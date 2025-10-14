# Git Branching Strategy

Optimize for focus and fast learning. Everything else is deferred.

## Active Branch Types
```
main                     # Stable, only merged reviewed work
feature/<issue>-<slug>   # Single focused change set
experiment/<spike>       # Throwaway ≤24h; summarize then delete
```

## Core Rules
1. One feature branch at a time (unless blocked & reason logged in issue).
2. Branch name MUST start with linked issue ID.
3. Squash merge (or consistent no-ff)—pick one; keep history linear.
4. Delete branch immediately after merge.
5. Experiments: no code polish, summary comment before deletion.

## Minimal Workflow
```
git checkout -b feature/123-signal-table
# work & commit
git push -u origin feature/123-signal-table
# open PR (#123 ...)
git checkout main && git pull --ff-only
git merge --squash feature/123-signal-table
git push origin main
git branch -D feature/123-signal-table
```
All merges to main MUST go through a Pull Request (PR).
Direct pushes/merges to main (even for docs) are prohibited.
Always link PRs to the related issue and artifact.

Example:
git checkout -b feature/123-signal-table # Work & commit
git push -u origin feature/123-signal-table # Open PR (#123 ...)

## Main Branch Protection

- Direct pushes/commits to `main` are prohibited for all users (including admins).
- All contributions to main must go through a Pull Request (PR).
- This is enforced by GitHub branch protection rules.

See repo settings (“Branches”) for rule details.


## Commit Format
```
<type>(<issue>-<scope>): <description>
feat(123-schema): add initial battery signal schema
docs(123-schema): clarify scaling factors
```
Types: feat | fix | docs | chore | refactor | test | perf

## When to Use experiment/
| Situation | Use? | Example |
|-----------|------|---------|
| Quick library viability test | ✅ | experiment/cantools-check |
| Pure docs/pseudocode | ❌ | Do on feature branch |
| Risky refactor spike | ✅ | experiment/batch-loop-alt |

## Quality Gate Before Merge
* Intentional file set only (git diff --stat main..HEAD)
* Basic run / manual curl ok
* README / ADR updated if claim changed

## Daily Flow
```
Is issue conceptual? -> Write docs/pseudocode first
Blocked? -> Document block → (optional) start second branch
Done? -> Squash merge → close issue → log reflection → delete branch
New idea? -> Create issue first; no ad-hoc commits
```

## Scale-Up (Ignore Until Triggered)
Add `develop`, release branches, epics ONLY when: ≥2 contributors OR parallel release stabilization needed. Until then, this section is inert.

Stay lean; branching should disappear into the background of learning.
