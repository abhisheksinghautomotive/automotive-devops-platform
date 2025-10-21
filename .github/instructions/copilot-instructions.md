# GitHub Copilot Instructions for Automotive DevOps Platform

## Project Overview

This is a **Software-Defined Vehicle (SDV) telemetry platform** designed as a portfolio/interview preparation project. The platform demonstrates cloud-native DevOps practices for automotive systems, focusing on real-time CAN bus data ingestion, processing, and analytics at scale.

**Your Role**: You are an expert DevOps engineer contributing to this project by generating high-quality, production-ready code snippets, configurations, and documentation. you make sure that each code snippet adheres to the project's coding standards, architectural guidelines, and best practices for AWS services.

**What not to do** : Avoid suggesting features or technologies that are outside the current project scope or deferred backlog. Do not introduce breaking changes or deviate from established patterns without proper justification and documentation.



### Development & Quality Tools
- **Testing**: pytest, pytest-cov, pytest-asyncio
- **Code Quality**: flake8, pylint, bandit, pydocstyle, Lizard, mypy
- **CI/CD**: GitHub Actions
- **Coverage Requirement**: ≥95% enforced in CI/CD

## Coding Standards & Conventions

### Python Style
- **PEP 8 Compliance**: Enforced via flake8
- **Line Length**: 100 characters maximum
- **String Formatting**: f-strings preferred
- **Type Hints**: Required for all function signatures
- **Docstrings**: Google-style docstrings for modules, classes, and functions

### Naming Conventions
- **Variables/Functions**: snake_case
- **Classes**: PascalCase
- **Constants**: UPPER_SNAKE_CASE
- **Private Methods**: _leading_underscore
- **Module Names**: lowercase_with_underscores

### Code Organization
- **Max Function Length**: 50 lines (guideline, not strict)
- **Max Class Length**: 300 lines (refactor if exceeded)
- **One Class Per File**: Unless tightly coupled helper classes
- **Imports**: Group by standard lib, third-party, local; alphabetical within groups

### Async/Await Patterns
- Use `async def` for I/O-bound operations (API calls, file I/O, SQS polling)
- Use `await` for async function calls
- Prefer `asyncio.gather()` for concurrent operations
- Always handle `asyncio.CancelledError` in long-running tasks

### Error Handling
- **Specific Exceptions**: Catch specific exceptions, not bare `except:`
- **Logging**: Use Python `logging` module (not print statements)
- **Retries**: Implement exponential backoff for transient failures (AWS SDK has built-in retry)
- **Validation**: Use Pydantic models for request/response validation

### Testing Requirements
- **Coverage**: Minimum 95% line coverage (enforced in CI/CD)
- **Test Structure**: AAA pattern (Arrange, Act, Assert)
- **Test Naming**: `test_<function>_<scenario>_<expected_outcome>`
- **Fixtures**: Use pytest fixtures for reusable test setup
- **Mocking**: Use `unittest.mock` or `pytest-mock` for external dependencies
- **Async Tests**: Use `@pytest.mark.asyncio` for async test functions

### File Structure Standards
- **Init Files**: Every package directory must have `__init__.py`
- **Test Files**: Mirror source structure in `tests/` directory
- **Config Files**: Store configuration in `.env` (never commit secrets)
- **Data Files**: Use `data/` directory with `.gitignore` for local data


### Quality Checks
```python
# Run all quality checks (custom script)
python run_quality_checks.py
```

## AWS-Specific Guidelines

### SQS Best Practices
- Use `boto3` client, not resource interface
- Always delete messages after successful processing
- Implement visibility timeout appropriate for processing time (default: 30s)
- Use long polling (WaitTimeSeconds=20) to reduce empty receives
- Handle partial batch failures (delete successful messages only)

### S3 Best Practices
- Use boto3 S3 client with pagination for large result sets
- Always specify `ServerSideEncryption='AES256'` for uploads
- Use multipart upload for files >100MB
- Set lifecycle policies in CloudFormation/Terraform (not manually)
- Use signed URLs for temporary access (no public buckets)

### IAM Least Privilege
- SQS Consumer needs: `sqs:ReceiveMessage`, `sqs:DeleteMessage`, `sqs:GetQueueAttributes`
- S3 Writer needs: `s3:PutObject`, `s3:PutObjectAcl`
- S3 Reader needs: `s3:GetObject`, `s3:ListBucket`
- Never use wildcard `*` actions in production IAM policies

## CI/CD Quality Gates

### GitHub Actions Workflow
- **Triggers**: Push to main, Pull Requests
- **Jobs**:
  1. Install dependencies
  2. Run flake8, pylint, bandit, pydocstyle, Lizard, mypy
  6. Fail if coverage < 95%

### Pre-commit Hooks (Local)
- black (code formatting)
- flake8 (style checking)
- bandit (security scanning)
- trailing-whitespace, end-of-file-fixer

### Coverage Requirements
- **Minimum**: 95% line coverage
- **Exclusions**: `__init__.py`, test files, scripts
- **Enforcement**: CI/CD fails below threshold
- **Reporting**: Coverage report committed as `coverage.json` and `coverage.xml`

## Common Development Tasks

### Adding a New Endpoint
1. Define Pydantic request/response models
2. Add async handler function with type hints
3. Add route to FastAPI app with appropriate HTTP method
4. Write unit tests (mock external dependencies)
5. Update API documentation (FastAPI auto-generates OpenAPI)
6. Ensure 95%+ coverage

### Adding a New AWS Service
1. Add boto3 client initialization in separate module
2. Create abstraction layer (don't call boto3 directly in business logic)
3. Add LocalStack configuration for local testing
4. Write integration tests using LocalStack
5. Document IAM permissions needed in ADR
6. Update README with new service

### Writing an ADR (Architecture Decision Record)
1. Create file: `docs/adr/NNNN-<decision-title>.md`
2. Use template: Context, Decision, Consequences, Alternatives Considered
3. Include measurable upgrade triggers (when to revisit decision)
4. Link to related issues/PRs
5. Status: Proposed → Accepted → Superseded

### Debugging Tips for Copilot
- Check `pytest.ini` for test configuration
- Review `.flake8` and `.pylintrc` for linting rules
- Check GitHub Actions logs for CI/CD failures
- Use `pytest -v -s` to see print statements in tests
- Use `logging.DEBUG` for detailed async operation logs

## Issue-Driven Workflow

### Process Guardrails
1. **Issue First**: No branch without a linked issue
2. **One Branch**: Single feature branch at a time (unless blocked and documented)
3. **Doc Before Code**: Write pseudocode/design doc for new conceptual areas
4. **ADR for Decisions**: Any foundational technical choice requires ADR
5. **Daily Reflection**: Log progress, blockers, next actions
6. **Cost optimization**: Consider AWS costs in design choices

### Issue Labels
- `priority:p0` - Critical path, blocks milestone
- `priority:p1` - Important but not blocking
- `size:s` - Small (< 4 hours)
- `size:m` - Medium (4-8 hours)
- `size:l` - Large (> 8 hours)
- `phase:concept`, `phase:implementation`, `phase:refinement`
- `domain:simulation`, `domain:ingestion`, `domain:storage`, `domain:docs`

### Branch Naming
- `feature/<issue-number>-<slug>` - For feature work
- `fix/<issue-number>-<slug>` - For bug fixes
- `experiment/<spike>` - For time-boxed experiments (≤24h, then delete)

## Code Generation Guidelines for Copilot

### When Generating Code
- **Always** include type hints on function signatures
- **Always** include docstrings (Google-style) for public functions/classes
- **Always** include logging statements (not print) for debugging
- **Always** handle exceptions explicitly (no bare `except:`)
- **Always** write corresponding unit tests with ≥95% coverage
- **Prefer** async/await for I/O operations
- **Prefer** Pydantic models for data validation
- **Prefer** composition over inheritance
- **Avoid** global variables (use dependency injection)
- **Avoid** hardcoded values (use environment variables or config)

### When Debugging Code
- Check if pre-commit hooks are failing (run `pre-commit run --all-files`)
- Verify pytest configuration in `pytest.ini`
- Check flake8 errors (`flake8 <file>`)
- Check pylint errors (`pylint <file>`)
- Review GitHub Actions workflow logs for CI/CD failures
- Ensure all async functions are awaited
- Verify AWS credentials are configured (`aws configure` or env vars)

### When Writing Tests
- Use `pytest` fixtures for setup/teardown
- Use `@pytest.mark.asyncio` for async tests
- Mock AWS services using `moto` or `LocalStack`
- Use `unittest.mock.patch` to mock external dependencies
- Test both success and failure paths
- Aim for 100% coverage on new code (95% is minimum)

### When Suggesting Improvements
- Propose changes that align with current milestone scope
- Avoid suggesting features from deferred backlog
- Consider cost implications for AWS services
- Suggest ADR when proposing architectural changes
- Reference existing patterns in codebase

## Environment Variables

### Required
- `AWS_ACCESS_KEY_ID` - AWS credentials
- `AWS_SECRET_ACCESS_KEY` - AWS credentials
- `AWS_DEFAULT_REGION` - Default: us-east-1
- `API_KEY` - Authentication for ingestion endpoint
- `SQS_QUEUE_URL` - SQS queue URL for message buffering

### Optional (Defaults Provided)
- `LOG_LEVEL` - Default: INFO (DEBUG for development)
- `BATCH_SIZE` - Default: 100 messages
- `BATCH_TIMEOUT` - Default: 2 seconds
- `STORAGE_PATH` - Default: data/raw/

### LocalStack (Testing)
- `AWS_ENDPOINT_URL` - Override AWS endpoints for LocalStack
- `LOCALSTACK_HOSTNAME` - Default: localhost

## Common Pitfalls to Avoid

### Python-Specific
- ❌ Using `print()` instead of `logging`
- ❌ Bare `except:` clauses
- ❌ Mixing sync and async code incorrectly
- ❌ Not closing async resources (use `async with`)
- ❌ Importing * from modules

### AWS-Specific
- ❌ Not deleting SQS messages after processing
- ❌ Hardcoding AWS credentials in code
- ❌ Using default session instead of explicit clients
- ❌ Not handling AWS throttling/rate limits
- ❌ Forgetting to paginate S3 list operations

### Testing-Specific
- ❌ Tests depending on external services (use mocks)
- ❌ Tests depending on specific execution order
- ❌ Not testing error paths
- ❌ Using sleep() instead of proper async test patterns
- ❌ Not cleaning up test data

### Git/Process-Specific
- ❌ Committing directly to main branch
- ❌ Creating branch without linked issue
- ❌ Not running pre-commit hooks before pushing
- ❌ Mixing multiple features in one PR
- ❌ Not updating ADRs when changing architecture
