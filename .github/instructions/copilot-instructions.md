# GitHub Copilot Instructions for Automotive DevOps Platform

## Project Overview

This is a **Software-Defined Vehicle (SDV) telemetry platform** designed as a portfolio/interview preparation project. The platform demonstrates cloud-native DevOps practices for automotive systems, focusing on real-time CAN bus data ingestion, processing, and analytics at scale.

**Current Status**: Project 01 (CAN Data Platform) - Building core MVP pipeline with SQS integration.

**Target Audience**: Tier-1 product companies, SaaS, and automotive/mobility engineering roles (DevOps, Platform Engineering, Site Reliability Engineering).

## Project Structure

```
automotive-devops-platform/
├── .github/
│   ├── workflows/
│   │   └── code-quality.yml          # CI/CD quality enforcement
│   ├── instructions/                  # Path-specific Copilot instructions
│   └── copilot-instructions.md        # This file
├── projects/
│   └── can_data_platform/             # Project 01: Active development
│       ├── src/                       # Source code modules
│       │   ├── generator/             # Battery telemetry simulator
│       │   ├── receiver/              # FastAPI ingestion endpoint
│       │   ├── consumer/              # SQS batch consumer
│       │   └── aggregator/            # Data aggregation scripts
│       ├── scripts/                   # Utility scripts
│       ├── data/                      # Local data storage (JSONL)
│       ├── docs/                      # Project-specific documentation
│       └── README.md                  # Project documentation
├── docs/
│   ├── adr/                           # Architecture Decision Records
│   └── architecture/                  # System design documents
├── tests/                             # Unit and integration tests
├── progress-tracking/
│   └── daily-log.md                   # Development journal
├── requirements.txt                   # Production dependencies
├── requirements-test.txt              # Testing dependencies
├── pytest.ini                         # Pytest configuration
├── .pre-commit-config.yaml            # Pre-commit hooks
├── .flake8                            # Flake8 configuration
├── .pylintrc                          # Pylint configuration
└── README.md                          # Main project documentation
```

## Technology Stack

### Core Technologies
- **Language**: Python 3.9+
- **Web Framework**: FastAPI (async REST API)
- **Message Queue**: AWS SQS (Standard Queue)
- **Storage**: 
  - Local: JSONL files (time-partitioned)
  - Cloud: AWS S3 (with lifecycle policies - in progress)
- **Data Processing**: Batch processing with asyncio

### Development & Quality Tools
- **Testing**: pytest, pytest-cov, pytest-asyncio
- **Code Quality**: flake8, pylint, bandit (security)
- **Pre-commit Hooks**: black, isort, flake8, bandit
- **CI/CD**: GitHub Actions
- **Coverage Requirement**: ≥95% enforced in CI/CD

### AWS Services (Current & Planned)
- **SQS**: Message buffering and decoupling
- **S3**: Long-term data storage with lifecycle policies
- **IAM**: Least-privilege access control
- **LocalStack**: Local AWS emulation for testing

### Future Stack (Deferred)
- Docker/Docker Compose
- Kubernetes (EKS)
- Terraform (IaC)
- Grafana/Prometheus (Observability)
- Jenkins/GitHub Actions (Advanced CI/CD)

## Coding Standards & Conventions

### Python Style
- **PEP 8 Compliance**: Enforced via flake8
- **Line Length**: 100 characters maximum
- **Import Ordering**: isort (standard → third-party → local)
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

## Architecture Patterns

### Data Flow (Current MVP)
```
Battery Simulator → FastAPI Receiver → AWS SQS → Batch Consumer → JSONL (S3) → Aggregation
```

### Time-Partitioned Storage
- Path format: `data/raw/year=YYYY/month=MM/day=DD/hour=HH/batch-<timestamp>.jsonl`
- Enables efficient querying and lifecycle management
- Always use UTC timestamps

### Batching Strategy
- **Batch Size**: Poll up to 100 messages OR 2-second timeout (whichever comes first)
- **Flush Trigger**: Batch full OR timeout reached
- **File Rotation**: Create new file if current file exceeds ~5MB

### API Design
- **REST Conventions**: Use appropriate HTTP methods (POST for ingestion)
- **Authentication**: API key via custom header `X-API-Key`
- **Response Format**: JSON with consistent structure
- **Error Responses**: Include error code, message, and request_id
- **Health Endpoint**: Always include `/health` endpoint returning 200 OK

### Data Schema (Current)
```json
{
  "timestamp": "2025-10-19T12:34:56.123Z",  // ISO 8601 UTC
  "vehicle_id": "veh-00123",                 // String identifier
  "can_id": "0x1F0",                         // Hex CAN message ID
  "payload": {                                // Decoded signals
    "battery_soc": 85.5,
    "battery_voltage": 400.2,
    "battery_current": -15.3
  },
  "ingest_received_at": "2025-10-19T12:34:56.200Z"  // Server-side timestamp
}
```

### Metrics & Observability
- **Latency Tracking**: Log P50, P95, P99 latencies for each batch
- **Message Counts**: Track messages per minute/hour
- **Error Rates**: Log and monitor error percentages
- **Queue Depth**: Monitor SQS ApproximateNumberOfMessages

## Build & Testing Commands

### Local Development
```bash
# Setup virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scriptsctivate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-test.txt

# Run pre-commit checks manually
pre-commit run --all-files

# Run application (adjust path based on module)
uvicorn projects.can_data_platform.src.receiver.app:app --reload
```

### Testing
```bash
# Run all tests with coverage
pytest

# Run tests with verbose output
pytest -v

# Run specific test file
pytest tests/test_generator.py

# Run tests matching pattern
pytest -k "test_battery"

# Generate coverage report
pytest --cov=projects/can_data_platform/src --cov-report=html
```

### Quality Checks
```bash
# Run all quality checks (custom script)
./run_quality_checks.sh

# Individual tools
flake8 projects/can_data_platform/src
pylint projects/can_data_platform/src
bandit -r projects/can_data_platform/src
```

### Git Workflow
```bash
# Create feature branch (always linked to issue)
git checkout -b feature/<issue-number>-<short-description>

# Commit with conventional commits format
git commit -m "feat: add SQS batch consumer with latency tracking (#71)"
git commit -m "fix: resolve SQS message deletion race condition (#72)"
git commit -m "docs: update ADR 0001 with SQS decision (#75)"

# Pre-commit hooks run automatically on commit
# Push and create PR
git push origin feature/<issue-number>-<short-description>
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
  2. Run flake8 (linting)
  3. Run pylint (static analysis)
  4. Run bandit (security scanning)
  5. Run pytest with coverage
  6. Fail if coverage < 95%

### Pre-commit Hooks (Local)
- black (code formatting)
- isort (import sorting)
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

## Current Milestone Context (P01-Core-Pipeline-MVP)

### Active Work (Due: Oct 26, 2025)
- Implementing SQS integration for message buffering
- Building batch consumer with JSONL output
- Adding end-to-end latency tracking (P50/P95/P99)
- Creating hourly aggregation script
- Writing integration tests for full pipeline

### Success Criteria
- Process 1,000+ events through SQS → JSONL pipeline (zero loss)
- P95 end-to-end latency < 5 seconds
- Generate at least one hourly aggregate output file
- Maintain ≥95% code coverage
- Mark ADR 0001 (SQS Transport Decision) as "Accepted"

### Deferred Features (Post-MVP)
- Kafka/Kinesis streaming
- Real-time dashboards (Grafana)
- Parquet file format
- Multi-region deployment
- Advanced monitoring (CloudWatch/Datadog)
- Container orchestration (Kubernetes)

## Interview Preparation Focus

### Key Technical Stories to Support
1. **SQS vs Kinesis vs Kafka Trade-offs**: Cost, operational overhead, ordering guarantees
2. **Batch vs Stream Processing**: MVP latency targets, engineering effort vs real-time needs
3. **Local → Cloud Storage Migration**: S3 lifecycle policies, cost optimization
4. **Test Coverage Discipline**: 95% enforcement, CI/CD quality gates
5. **MVP Scoping**: What to defer, measurable upgrade triggers

### Architecture Decision Rationale
- **Why SQS Standard?** Simplicity + cost over ordering guarantees (upgrade trigger: >5% duplicates)
- **Why JSONL?** Human-readable, line-delimited for streaming, schema evolution
- **Why Batch Consumer?** P95 latency <5s sufficient for analytics use case
- **Why S3 Lifecycle?** Cost optimization: Standard → IA (30d) → Glacier (90d)

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

## Project Philosophy & Constraints

### MVP-First Mindset
- Ship working MVP before adding sophistication
- Document upgrade triggers (when to revisit simple solutions)
- Defer features to Post-MVP Backlog unless interview-critical
- Focus on explainability over complexity

### Cost Consciousness
- Use SQS Standard (not FIFO) unless ordering required
- Use S3 lifecycle policies for cost optimization
- Use LocalStack for testing (avoid AWS dev costs)
- Monitor AWS Free Tier limits

### Interview-Ready Code
- Every component should be "whiteboardable"
- Document trade-off decisions in ADRs
- Maintain artifacts for portfolio (diagrams, metrics, demo scripts)
- Write code you can explain in system design interviews

### Quality Over Speed
- Never compromise on 95% test coverage
- Pre-commit hooks prevent bad commits
- CI/CD blocks merges below quality threshold
- Issue-first workflow prevents scope creep

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

## Additional Resources

### Documentation Locations
- **ADRs**: `docs/adr/` - Architecture decisions with context
- **API Specs**: Auto-generated at `/docs` endpoint (FastAPI)
- **Project READMEs**: Each project has detailed README
- **Progress Tracking**: `progress-tracking/daily-log.md`

### External References
- FastAPI Docs: https://fastapi.tiangolo.com/
- boto3 SQS: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sqs.html
- boto3 S3: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html
- pytest: https://docs.pytest.org/
- LocalStack: https://docs.localstack.cloud/

### Code Review Checklist
- [ ] All functions have type hints and docstrings
- [ ] Code follows PEP 8 (verified by flake8)
- [ ] Test coverage ≥95% (verified by pytest-cov)
- [ ] No security issues (verified by bandit)
- [ ] Async operations properly awaited
- [ ] AWS resources properly cleaned up
- [ ] Environment variables used for config (no hardcoded values)
- [ ] Error handling includes logging
- [ ] PR linked to issue
- [ ] ADR updated if architectural change

---

**Last Updated**: October 19, 2025  
**Current Milestone**: P01-Core-Pipeline-MVP (Due: Oct 26, 2025)  
**Project Phase**: MVP Development → Cloud Integration → Interview Prep
