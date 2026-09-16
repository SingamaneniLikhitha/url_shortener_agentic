"""
Agentic SDLC orchestration control plane.

The orchestrator is intentionally provider-independent:
LLM/agent implementations can be plugged into the task handlers later,
while governance, state, approvals, retries and safety remain deterministic.
"""

from dataclasses import dataclass, field
from enum import Enum
from time import monotonic
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any
import uuid


class Status(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    BLOCKED = "blocked"
    APPROVAL = "approval"


@dataclass
class Task:
    id: str
    name: str
    deps: list[str] = field(default_factory=list)
    status: Status = Status.PENDING
    attempts: int = 0
    output: dict[str, Any] = field(default_factory=dict)


class AgenticOrchestrator:

    MAX_RETRIES = 2

    def __init__(self, scenario: str):
        self.run_id = str(uuid.uuid4())

        self.scenario = scenario
        self.started = monotonic()

        self.safe_stopped = False
        self.context: dict[str, Any] = {}

        self.audit: list[dict[str, Any]] = []

        self.metrics = {
            "success_rate": 0,
            "retry_count": 0,
            "rollback_count": 0,
            "mttr_ms": 0,
            "latency_ms": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
        }

        self.tasks = {
            "requirements": Task(
                "requirements",
                "Requirement Understanding"
            ),

            "architecture": Task(
                "architecture",
                "Architecture Design",
                ["requirements"]
            ),

            "implementation": Task(
                "implementation",
                "Implementation",
                ["architecture"]
            ),

            "tests": Task(
                "tests",
                "Test Generation and Validation",
                ["implementation"]
            ),

            "security": Task(
                "security",
                "Security Validation",
                ["implementation"]
            ),

            "validation": Task(
                "validation",
                "Quality Gate",
                ["tests", "security"]
            ),

            "docs": Task(
                "docs",
                "Documentation",
                ["architecture", "validation"]
            ),

            "release": Task(
                "release",
                "Release Readiness",
                ["docs"]
            ),
        }

    # ---------------------------------------------------------
    # Observability
    # ---------------------------------------------------------

    def log(self, event, task=None, detail=None):

        self.audit.append({
            "ts": round(monotonic(), 6),
            "event": event,
            "task": task,
            "detail": detail,
        })

    # ---------------------------------------------------------
    # Governance
    # ---------------------------------------------------------

    def policy_check(self, task_id: str):

        protected_tasks = {
            "implementation",
            "release"
        }

        if task_id in protected_tasks:

            self.log(
                "policy_check",
                task_id,
                {
                    "change_control": True,
                    "human_oversight": task_id == "release"
                }
            )

        return True

    # ---------------------------------------------------------
    # Requirement agent
    # ---------------------------------------------------------

    def requirements_agent(self):

        task = self.tasks["requirements"]

        task.status = Status.RUNNING

        self.log(
            "task_started",
            "requirements"
        )

        if self.scenario == "ambiguous":

            task.output = {
                "ambiguous": True,
                "questions": [
                    "Does permanent mean no expiry or immutable destination?",
                    "What scale and SLO are required?",
                    "What retention and abuse policy applies?"
                ],
                "decision": "human clarification required"
            }

            task.status = Status.APPROVAL

            self.log(
                "approval_required",
                "requirements",
                "clarification required before design"
            )

            return False

        if self.scenario == "brownfield":

            task.output = {
                "normalized": True,
                "scenario": "brownfield",
                "change_type": "enhancement",
                "analysis": [
                    "inspect existing URL API",
                    "identify persistence layer",
                    "identify analytics flow",
                    "preserve backward compatibility",
                    "add regression tests"
                ]
            }

        else:

            task.output = {
                "normalized": True,
                "scenario": "greenfield",
                "intent": "build URL shortening service",
                "constraints": [
                    "REST API",
                    "analytics",
                    "expiry",
                    "safe change management"
                ]
            }

        task.status = Status.PASSED

        self.log(
            "task_passed",
            "requirements",
            task.output
        )

        return True

    # ---------------------------------------------------------
    # Architecture agent
    # ---------------------------------------------------------

    def architecture_agent(self):

        task = self.tasks["architecture"]

        task.status = Status.RUNNING

        self.log(
            "task_started",
            "architecture"
        )

        if self.scenario == "brownfield":

            task.output = {
                "mode": "brownfield",
                "components": [
                    "existing API",
                    "existing persistence",
                    "analytics",
                    "orchestrator"
                ],
                "strategy": [
                    "preserve existing contracts",
                    "introduce change behind service boundary",
                    "add regression coverage",
                    "migrate incrementally"
                ],
                "risk": "backward compatibility"
            }

        else:

            task.output = {
                "mode": "greenfield",
                "components": [
                    "API",
                    "SQLite",
                    "analytics",
                    "orchestrator"
                ],
                "graph": "explicit DAG"
            }

        task.output["gates"] = [
            "requirements",
            "quality-validation",
            "human-release"
        ]

        task.status = Status.PASSED

        self.log(
            "task_passed",
            "architecture",
            task.output
        )

    # ---------------------------------------------------------
    # Implementation agent
    # ---------------------------------------------------------

    def implementation_agent(self):

        task = self.tasks["implementation"]

        self.policy_check("implementation")

        task.status = Status.RUNNING

        self.log(
            "task_started",
            "implementation"
        )

        task.output = {
            "artifact": "app/main.py",
            "change_strategy": (
                "incremental"
                if self.scenario == "brownfield"
                else "new implementation"
            ),
            "rollback": {
                "strategy": "git revert / previous immutable artifact",
                "automatic": False,
                "human_controlled": True
            }
        }

        task.status = Status.PASSED

        self.log(
            "task_passed",
            "implementation",
            task.output
        )

    # ---------------------------------------------------------
    # Test agent
    # ---------------------------------------------------------

    def tests_agent(self):

        task = self.tasks["tests"]

        task.status = Status.RUNNING

        self.log(
            "task_started",
            "tests"
        )

        task.output = {
            "agent": "test-agent",
            "unit": 12,
            "integration": 4,
            "contract": 3,
            "passed": 19,
            "coverage_gate": "passed",
            "regression_required": self.scenario == "brownfield"
        }

        task.status = Status.PASSED

        self.log(
            "task_passed",
            "tests",
            task.output
        )

    # ---------------------------------------------------------
    # Security agent
    # ---------------------------------------------------------

    def security_agent(self):

        task = self.tasks["security"]

        task.status = Status.RUNNING

        self.log(
            "task_started",
            "security"
        )

        task.output = {
            "agent": "security-agent",
            "checks": [
                "input validation",
                "alias collision",
                "expiry handling",
                "open redirect risk",
                "abuse controls",
                "safe-stop policy"
            ],
            "passed": True,
            "critical_findings": 0
        }

        task.status = Status.PASSED

        self.log(
            "task_passed",
            "security",
            task.output
        )

    # ---------------------------------------------------------
    # Parallel execution
    # ---------------------------------------------------------

    def run_parallel_validation(self):

        self.log(
            "parallel_branch_started",
            detail={
                "branches": [
                    "tests",
                    "security"
                ]
            }
        )

        with ThreadPoolExecutor(max_workers=2) as executor:

            futures = {
                executor.submit(self.tests_agent): "tests",
                executor.submit(self.security_agent): "security"
            }

            for future in as_completed(futures):

                task_id = futures[future]

                try:
                    future.result()

                except Exception as exc:

                    self.fail(
                        task_id,
                        str(exc)
                    )

        self.log(
            "parallel_branch_synchronized",
            detail={
                "join": "validation",
                "dependencies": [
                    "tests",
                    "security"
                ]
            }
        )

    # ---------------------------------------------------------
    # Failure / retry / safe-stop
    # ---------------------------------------------------------

    def fail(self, task_id: str, reason: str):

        task = self.tasks[task_id]

        task.attempts += 1

        self.metrics["retry_count"] += 1

        self.log(
            "task_failed",
            task_id,
            {
                "reason": reason,
                "attempt": task.attempts
            }
        )

        if task.attempts <= self.MAX_RETRIES:

            task.status = Status.PENDING

            self.log(
                "bounded_retry",
                task_id,
                {
                    "attempt": task.attempts,
                    "max_retries": self.MAX_RETRIES
                }
            )

        else:

            task.status = Status.FAILED

            self.safe_stopped = True

            self.metrics["tasks_failed"] += 1

            self.log(
                "safe_stop",
                task_id,
                "retry budget exhausted"
            )

            self.block_dependents(task_id)

    def block_dependents(self, task_id):

        for task in self.tasks.values():

            if (
                task_id in task.deps
                and task.status == Status.PENDING
            ):

                task.status = Status.BLOCKED

                self.log(
                    "task_blocked",
                    task.id,
                    f"dependency {task_id} failed"
                )

    # ---------------------------------------------------------
    # Quality gate
    # ---------------------------------------------------------

    def validation_gate(self):

        task = self.tasks["validation"]

        task.status = Status.RUNNING

        self.log(
            "gate_started",
            "validation"
        )

        tests_passed = (
            self.tasks["tests"].status == Status.PASSED
        )

        security_passed = (
            self.tasks["security"].status == Status.PASSED
        )

        if not tests_passed or not security_passed:

            task.status = Status.FAILED

            self.safe_stopped = True

            self.log(
                "safe_stop",
                "validation",
                "quality gate failed"
            )

            return False

        task.output = {
            "tests": "passed",
            "security": "passed",
            "policy": "passed",
            "release_candidate": True
        }

        task.status = Status.PASSED

        self.log(
            "gate_passed",
            "validation",
            task.output
        )

        return True

    # ---------------------------------------------------------
    # Documentation
    # ---------------------------------------------------------

    def docs_agent(self):

        task = self.tasks["docs"]

        task.status = Status.RUNNING

        self.log(
            "task_started",
            "docs"
        )

        task.output = {
            "artifacts": [
                "docs/ARCHITECTURE.md",
                "docs/SCENARIOS.md",
                "docs/FINAL_SUMMARY.md"
            ],
            "generated_from": [
                "architecture",
                "validation"
            ]
        }

        task.status = Status.PASSED

        self.log(
            "task_passed",
            "docs"
        )

    # ---------------------------------------------------------
    # Release gate
    # ---------------------------------------------------------

    def release_gate(self):

        task = self.tasks["release"]

        self.policy_check("release")

        task.status = Status.APPROVAL

        task.output = {
            "release_candidate": True,
            "requires_human_approval": True,
            "change_control": "required"
        }

        self.log(
            "approval_required",
            "release",
            "human approval required before production release"
        )

    # ---------------------------------------------------------
    # Human approval
    # ---------------------------------------------------------

    def approve_release(self):

        task = self.tasks["release"]

        if task.status != Status.APPROVAL:

            return False

        task.status = Status.PASSED

        task.output["approved_by"] = "human"

        self.log(
            "human_approval",
            "release",
            "approved"
        )

        self.finalize_metrics()

        return True

    # ---------------------------------------------------------
    # Dynamic re-planning
    # ---------------------------------------------------------

    def replan(self, reason: str):

        self.context["replan_reason"] = reason

        self.log(
            "replan_started",
            detail=reason
        )

        if "database contention" in reason.lower():

            self.context["architecture_change"] = {
                "from": "synchronous database writes",
                "to": "queue-based click aggregation",
                "reason": "reduce write contention"
            }

            self.tasks["architecture"].output[
                "alternative"
            ] = "queue + analytics store"

        elif "latency" in reason.lower():

            self.context["architecture_change"] = {
                "from": "synchronous analytics",
                "to": "asynchronous analytics",
                "reason": "reduce end-to-end latency"
            }

        else:

            self.context["architecture_change"] = {
                "strategy": "re-evaluate impacted downstream tasks"
            }

        self.log(
            "replan_completed",
            detail=self.context["architecture_change"]
        )

        return self.snapshot()

    # ---------------------------------------------------------
    # Metrics
    # ---------------------------------------------------------

    def finalize_metrics(self):

        completed = sum(
            task.status == Status.PASSED
            for task in self.tasks.values()
        )

        total_terminal = sum(
            task.status in {
                Status.PASSED,
                Status.FAILED
            }
            for task in self.tasks.values()
        )

        self.metrics["tasks_completed"] = completed

        self.metrics["success_rate"] = round(
            completed / total_terminal,
            3
        ) if total_terminal else 0

        self.metrics["latency_ms"] = round(
            (monotonic() - self.started) * 1000,
            2
        )

    # ---------------------------------------------------------
    # Main state-machine execution
    # ---------------------------------------------------------

    def run(self):

        self.log(
            "run_started",
            detail={
                "run_id": self.run_id,
                "scenario": self.scenario
            }
        )

        self.context = {
            "run_id": self.run_id,
            "scenario": self.scenario,
            "governance": {
                "human_release_approval": True,
                "safe_stop": True,
                "max_retries": self.MAX_RETRIES
            }
        }

        # GATE 1
        if not self.requirements_agent():

            self.finalize_metrics()

            return self.snapshot()

        # Sequential path
        self.architecture_agent()
        self.implementation_agent()

        # Parallel branches
        self.run_parallel_validation()

        # Synchronization / quality gate
        if not self.validation_gate():

            self.finalize_metrics()

            return self.snapshot()

        # Documentation
        self.docs_agent()

        # Human approval checkpoint
        self.release_gate()

        self.finalize_metrics()

        return self.snapshot()

    # ---------------------------------------------------------
    # Snapshot
    # ---------------------------------------------------------

    def snapshot(self):

        return {
            "run_id": self.run_id,

            "scenario": self.scenario,

            "state": (
    "SAFE_STOP"
    if self.safe_stopped
    else (
        "AWAITING_HUMAN_APPROVAL"
        if any(
            task.status == Status.APPROVAL
            for task in self.tasks.values()
        )
        else "COMPLETED"
    )
),

            "tasks": {
                task_id: {
                    "name": task.name,
                    "status": task.status.value,
                    "deps": task.deps,
                    "attempts": task.attempts,
                    "output": task.output
                }
                for task_id, task in self.tasks.items()
            },

            "metrics": self.metrics,

            "safe_stop": self.safe_stopped,

            "context": self.context,

            "audit": self.audit
        }