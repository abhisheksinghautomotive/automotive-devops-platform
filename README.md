# Automotive DevOps Platform

[![In Development](https://img.shields.io/badge/status-in%20development-yellow)](https://github.com/abhisheksinghautomotive/automotive-devops-platform)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![CI](https://github.com/abhisheksinghautomotive/automotive-devops-platform/workflows/Code%20Quality%20Gate%20&%20Coverage%20Enforcement/badge.svg)](https://github.com/abhisheksinghautomotive/automotive-devops-platform/actions)
[![Coverage](https://img.shields.io/badge/coverage-96%25-brightgreen)](https://github.com/abhisheksinghautomotive/automotive-devops-platform)

> **A comprehensive DevOps platform for Software-Defined Vehicles (SDVs), demonstrating enterprise-scale cloud-native infrastructure, CI/CD automation, and automotive compliance standards.**

---

## 🎯 Project Mission

Build a production-grade, interview-ready portfolio demonstrating **DevOps and Platform Engineering expertise** for automotive/mobility technology companies. This single-repo learning journey progresses through 6 increasingly complex projects, focusing on practical skills for **Tier-1 product companies, SaaS platforms, and automotive engineering roles**.

**Current Focus**: Project 01 – Cloud-native telemetry ingestion pipeline for connected vehicles.

---

## 🚀 Why This Exists

- **Practice professional architecture & Git hygiene** while building real-world systems
- **Produce interview-ready artifacts**: ADRs, system designs, metrics, demo videos
- **Master DevOps fundamentals**: Cloud infrastructure, CI/CD, containerization, IaC
- **Bridge automotive expertise** (CAN/DBC, testing, validation) with **cloud-native practices**
- **Tell compelling technical stories** about trade-offs, scaling, cost optimization

---

## 📊 Current Status (As of Oct 19, 2025)

### ✅ Completed (Milestones 1-4)
- [x] **P01-MVP-ingestion** (Oct 8) - FastAPI endpoint, API key auth, JSONL batching
- [x] **P01-simulation-ready** (Oct 17) - BMW battery DBC signals, physics-based model
- [x] **P01-refinement-loop-1** (Oct 24) - Module-level variance, realistic simulation
- [x] **P01-Model-Realism-Refinement** (Oct 21) - Enhanced telemetry generation

**Achievements**:
- 19 issues closed
- 96% test coverage with CI/CD enforcement
- Realistic battery telemetry simulator with module variance
- GitHub Actions quality gates (flake8, pylint, bandit)
- Pre-commit hooks for code quality

### 🔄 In Progress (Active Sprint)
- **P01-Core-Pipeline-MVP** (Due: Oct 26) - SQS integration, batch consumer, latency tracking
  - 8 open issues
  - Target: 1,000+ messages through pipeline, <5s P95 latency

### 📅 Upcoming (3-Week Hybrid Plan)
- **Week 2** (Oct 27-Nov 3): **P01-Cloud-Storage-S3** - S3 integration with lifecycle policies
- **Week 3** (Nov 4-10): **P01-README + Demos + Interview Prep** - Documentation, demo video, Q&A prep

---

## 🛠️ Technology Stack

### Current (Project 01)
| Category | Technology |
|----------|------------|
| **Language** | Python 3.9+ |
| **Web Framework** | FastAPI (async) |
| **Message Queue** | AWS SQS (Standard) |
| **Storage** | JSONL (local) → AWS S3 |
| **Testing** | pytest, pytest-cov, pytest-asyncio |
| **Code Quality** | flake8, pylint, bandit, black, isort |
| **CI/CD** | GitHub Actions |
| **Coverage** | 96% (enforced ≥95%) |

### Future Projects (Deferred)
| Project | Technologies |
|---------|-------------|
| **02 - Testing** | Docker, Docker Compose, Selenium, pytest-xdist |
| **03 - CI/CD** | Jenkins, GitHub Actions, SonarQube, Nexus |
| **04 - K8s** | Kubernetes, Helm, ArgoCD, Prometheus, Grafana |
| **05 - IaC** | Terraform, CloudFormation, Ansible |
| **06 - Platform** | All of the above + service mesh, observability |

---

## 📋 Project Roadmap

| ID | Project | Status | Timeline | Focus |
|----|---------|--------|----------|-------|
| **01** | **CAN Data Platform** | 🔄 **In Progress** | Oct 8 - Nov 10 | Cloud-native ingestion, SQS, S3, latency tracking |
| 02 | Containerized Test Suite | ⏸️ Deferred | TBD | Docker, test automation, parallel execution |
| 03 | Enterprise CI/CD | ⏸️ Deferred | TBD | Jenkins pipelines, GitOps, security scanning |
| 04 | Kubernetes Platform | ⏸️ Deferred | TBD | EKS, Helm, service mesh, autoscaling |
| 05 | Infrastructure as Code | ⏸️ Deferred | TBD | Terraform, multi-cloud, cost optimization |
| 06 | SDV Platform Rollup | ⏸️ Deferred | TBD | Full platform integration, OTA updates |

---
