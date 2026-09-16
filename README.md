# Agentic URL Shortener

A runnable URL shortener prototype combined with a stateful, provider-independent agentic SDLC orchestration control plane.

The project demonstrates how software-engineering tasks can be decomposed, executed, validated, governed, and audited through an explicit workflow with human oversight.

## Key Capabilities

- URL shortening REST API
- Custom aliases
- URL expiration
- Click analytics
- SQLite persistence with WAL mode
- Explicit dependency graph (DAG)
- Sequential and parallel execution paths
- Parallel test and security validation
- Synchronization through a quality gate
- Greenfield, brownfield, and ambiguous scenarios
- Human approval checkpoint before release
- Bounded retries
- Safe-stop behavior after retry exhaustion
- Rollback strategy
- Dynamic re-planning
- Audit-grade execution trace
- Reliability and execution metrics
- Automated API and orchestration tests

## Architecture

The orchestration workflow follows this dependency graph:

```text
Requirements
     |
     v
Architecture
     |
     v
Implementation
     |
     +-------------------+
     |                   |
     v                   v
   Tests             Security
     |                   |
     +---------+---------+
               |
               v
        Quality Validation
               |
               v
        Documentation
               |
               v
     Human Release Approval
               |
               v
            Release
