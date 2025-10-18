# Branch Protection Rules for main branch
# These rules should be configured in GitHub repository settings

## Required Status Checks
- Code Quality Gate & Coverage Enforcement / Quality Gate & Testing (3.9)
- Code Quality Gate & Coverage Enforcement / Quality Gate & Testing (3.10) 
- Code Quality Gate & Coverage Enforcement / Quality Gate & Testing (3.11)
- Code Quality Gate & Coverage Enforcement / Quality Gate Summary
- Code Quality Gate & Coverage Enforcement / Integration Test Readiness

## Branch Protection Settings (Solo Developer)
- ✅ Require status checks to pass before merging
- ✅ Require branches to be up to date before merging  
- ☐ Require pull request reviews before merging (NOT needed for solo dev)
- ☐ Dismiss stale PR approvals when new commits are pushed (NOT applicable)
- ☐ Require review from code owners (NOT needed for solo dev)
- ☐ Restrict pushes that create files larger than 100MB (optional)
- ☐ Require signed commits (optional for solo dev)

## Auto-merge Prevention
- ❌ Allow force pushes (disabled)
- ❌ Allow deletions (disabled)

## Quality Gate Requirements
- Flake8: Zero PEP 8 violations
- Pylint: Score ≥9.5 for source, ≥8.0 for tests  
- Pydocstyle: All docstrings compliant
- Lizard: CCN ≤8, Length ≤100, Args ≤6
- Security: No HIGH severity Bandit issues
- Coverage: ≥95% line coverage required
- Tests: All unit tests must pass

## Configuration Commands (GitHub CLI - Solo Developer)
```bash
# Enable branch protection with required status checks (no PR reviews required)
gh api repos/:owner/:repo/branches/main/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["Quality Gate & Testing (3.9)","Quality Gate & Testing (3.10)","Quality Gate & Testing (3.11)","Quality Gate Summary","Integration Test Readiness"]}' \
  --field enforce_admins=true \
  --field required_pull_request_reviews=null \
  --field restrictions=null
```