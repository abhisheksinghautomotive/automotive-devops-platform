# SonarQube Quality Gate Configuration
# This file documents the quality gate settings that should be configured in SonarQube Cloud
# to match the existing quality standards of the Automotive DevOps Platform

## Coverage Requirements
# - Overall Coverage: >= 95% (matches pytest --cov-fail-under=95)
# - New Code Coverage: >= 95%
# - Coverage on New Code: >= 95%

## Reliability
# - Bugs: 0 (A rating)
# - New Bugs: 0

## Security
# - Vulnerabilities: 0 (A rating)
# - Security Hotspots Reviewed: >= 100%
# - New Vulnerabilities: 0
# - New Security Hotspots: 0

## Maintainability
# - Code Smells: <= 50 (A rating equivalent)
# - New Code Smells: <= 5
# - Technical Debt Ratio: <= 5%
# - Technical Debt Ratio on New Code: <= 5%

## Duplications
# - Duplicated Lines (%): <= 3%
# - Duplicated Lines on New Code (%): <= 3%

## Size Restrictions
# - Lines of Code: Information only (no gate)
# - New Lines of Code: Information only (no gate)

## Quality Gate Conditions JSON Export
# This can be imported into SonarQube Cloud if needed
{
  "conditions": [
    {
      "metric": "coverage",
      "op": "LT",
      "error": "95"
    },
    {
      "metric": "new_coverage",
      "op": "LT", 
      "error": "95"
    },
    {
      "metric": "bugs",
      "op": "GT",
      "error": "0"
    },
    {
      "metric": "new_bugs",
      "op": "GT",
      "error": "0"
    },
    {
      "metric": "vulnerabilities",
      "op": "GT", 
      "error": "0"
    },
    {
      "metric": "new_vulnerabilities",
      "op": "GT",
      "error": "0"
    },
    {
      "metric": "security_hotspots_reviewed",
      "op": "LT",
      "error": "100"
    },
    {
      "metric": "duplicated_lines_density",
      "op": "GT",
      "error": "3"
    },
    {
      "metric": "new_duplicated_lines_density", 
      "op": "GT",
      "error": "3"
    }
  ]
}