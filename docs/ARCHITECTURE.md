# Architecture

## 1. System Overview

The prototype contains two logical subsystems:

1. A customer-facing URL shortening service
2. An agentic SDLC orchestration control plane

The URL service provides URL creation, resolution, expiration and analytics.

The orchestration control plane models software-engineering execution as a governed state machine with explicit dependencies, sequential and parallel execution, validation gates, human approval, failure handling, audit lineage and dynamic re-planning.

---

## 2. URL Shortener

The prototype uses FastAPI with SQLite persistence.

### APIs

```text
POST /api/urls
GET  /r/{code}
GET  /api/urls/{code}/analytics
GET  /health