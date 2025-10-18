# 🎯 Code Quality Gates & CI/CD Enforcement

## Overview

This document outlines the strict code quality gates enforced in our CI/CD pipeline. **ALL quality checks must pass before any PR can be merged into the main branch.**

## 🚫 Merge Prevention Strategy

### GitHub Actions Workflow Protection
Our `code-quality.yml` workflow implements a **fail-fast strategy** that:
- Runs on every PR targeting `main` branch
- Executes across Python 3.9, 3.10, and 3.11 for compatibility
- **BLOCKS merge** if ANY quality check fails
- Provides detailed failure reporting in GitHub PR comments

### Branch Protection Rules
Configure these settings in GitHub repository settings:

```bash
# Required status checks (ALL must pass)
✅ Code Quality Gate & Coverage Enforcement / Quality Gate & Testing (3.9)
✅ Code Quality Gate & Coverage Enforcement / Quality Gate & Testing (3.10)  
✅ Code Quality Gate & Coverage Enforcement / Quality Gate & Testing (3.11)
✅ Code Quality Gate & Coverage Enforcement / Quality Gate Summary
✅ Code Quality Gate & Coverage Enforcement / Integration Test Readiness

# Protection settings (Solo Developer Configuration)
✅ Require status checks to pass before merging
✅ Require branches to be up to date before merging
☐ Require pull request reviews (NOT needed for solo dev)
☐ Dismiss stale reviews (NOT applicable for solo dev)
❌ Allow force pushes (DISABLED)
❌ Allow deletions (DISABLED)
```

## 📊 Quality Gate Requirements

### 1. 🔍 Security Analysis (Bandit)
- **Requirement**: Zero HIGH severity security issues
- **Failure Condition**: Any HIGH severity vulnerability detected
- **Command**: `bandit -r projects/ --severity-level medium`

### 2. 📝 PEP 8 Compliance (Flake8)  
- **Requirement**: Zero code style violations
- **Failure Condition**: Any flake8 error detected
- **Command**: `flake8 projects/ tests/ --count --statistics`

### 3. 🔬 Code Quality (Pylint)
- **Source Code**: Score ≥9.5/10 (STRICT)
- **Test Code**: Score ≥8.0/10 
- **Failure Condition**: Score below threshold
- **Command**: `pylint projects/ --fail-under=9.5`

### 4. 📚 Documentation (Pydocstyle)
- **Requirement**: All docstrings must follow conventions
- **Failure Condition**: Any docstring violation
- **Command**: `pydocstyle projects/ tests/`

### 5. 🧮 Complexity Analysis (Lizard)
- **Cyclomatic Complexity**: ≤8 (down from default 15)
- **Function Length**: ≤100 lines
- **Parameter Count**: ≤6 arguments
- **Failure Condition**: Any function exceeding limits
- **Command**: `lizard projects/ --CCN 8 --length 100 --arguments 6`

### 6. 🧪 Unit Tests
- **Requirement**: ALL tests must pass
- **Failure Condition**: Any test failure or error
- **Timeout**: 15 minutes max execution
- **Command**: `pytest tests/unit/ --strict-markers --maxfail=3`

### 7. 📊 Test Coverage (CRITICAL)
- **Requirement**: ≥95% line coverage (RAISED from 90%)
- **Failure Condition**: Coverage below 95%
- **Validation**: Double-checked via coverage.json parsing
- **Command**: `pytest --cov=projects/ --cov-fail-under=95`

## 🚨 Failure Handling

### Immediate PR Blocking
When quality gates fail:
1. **GitHub Actions fails** with clear error messages
2. **PR merge button disabled** automatically
3. **Detailed report** posted as PR comment
4. **Coverage report** shows exact missing lines
5. **Security issues** highlighted with severity levels

### Quality Gate Summary
The workflow generates a comprehensive summary:

```markdown
## 🎯 Code Quality Gate Results

| Quality Check | Requirement | Status |
|---------------|-------------|--------|
| 🔍 Security Scan | No HIGH severity issues | ❌ **FAILED** |
| 📝 Flake8 (PEP 8) | Zero violations | ✅ **PASSED** |
| 🔬 Pylint | Score ≥9.5 (src) ≥8.0 (tests) | ❌ **FAILED** |
| 📚 Pydocstyle | All docstrings compliant | ✅ **PASSED** |
| 🧮 Lizard Complexity | CCN ≤8, Length ≤100 | ✅ **PASSED** |
| 🧪 Unit Tests | All tests pass | ✅ **PASSED** |
| 📊 Test Coverage | ≥95% line coverage | ❌ **FAILED** |

### ❌ **QUALITY GATE FAILURE**
🚫 **PR cannot be merged until all quality checks pass**
```

## 🛠️ Local Development Setup

### Pre-commit Hooks
Install local quality checks:
```bash
pip install pre-commit
pre-commit install
```

### Manual Quality Check
Run the same checks locally:
```bash
# Use our quality script
./run_quality_checks.sh

# Or individual commands
flake8 projects/ tests/
pylint projects/ --fail-under=9.5
pytest --cov=projects/ --cov-fail-under=95
pydocstyle projects/ tests/
lizard projects/ --CCN 8
bandit -r projects/
```

## 📈 Quality Metrics Tracking

### Coverage Reporting
- **HTML Report**: Uploaded as GitHub Actions artifact
- **XML Report**: For external tools integration  
- **PR Comments**: Automatic coverage comparison
- **Badge Generation**: Updated on main branch merges

### Artifact Retention
- Test results: 30 days
- Coverage reports: 30 days  
- Security scans: 30 days
- Coverage badges: 90 days

## 🚀 Workflow Optimization

### Performance Features
- **Concurrency Control**: One workflow per PR
- **Matrix Strategy**: Parallel Python version testing
- **Fail-fast**: Stop on first failure
- **Path Filtering**: Only run on relevant changes
- **Dependency Caching**: Faster pip installs

### Monitoring
```yaml
timeout-minutes: 15  # Prevent runaway workflows
maxfail: 3          # Stop after 3 test failures  
durations: 10       # Report slowest tests
```

## 🎯 Success Criteria

**A PR can ONLY be merged when:**
1. ✅ All Python versions (3.9, 3.10, 3.11) pass
2. ✅ Security scan shows no HIGH severity issues
3. ✅ Flake8 reports zero violations
4. ✅ Pylint scores ≥9.5 (source) and ≥8.0 (tests)
5. ✅ All docstrings follow pydocstyle conventions
6. ✅ No functions exceed complexity/length limits
7. ✅ All unit tests pass without errors
8. ✅ Test coverage reaches or exceeds 95%
9. ✅ At least 1 code reviewer approves
10. ✅ Branch is up-to-date with main

## 📞 Support

If quality gates fail:
1. **Check GitHub Actions logs** for detailed error messages
2. **Run quality checks locally** to debug issues
3. **Review coverage report** to identify missing tests
4. **Use pre-commit hooks** to catch issues before pushing
5. **Ask for help** in PR comments if needed

**Remember: These quality gates ensure our automotive platform maintains the highest standards for safety-critical software development.**