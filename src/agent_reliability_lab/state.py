from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(slots=True)
class ToolSpec:
    name: str
    description: str
    executor: Callable[[dict[str, Any]], Any]
    requires_approval: bool = False
    max_retries: int = 0
    risk_level: str = "low"

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "requires_approval": self.requires_approval,
            "max_retries": self.max_retries,
            "risk_level": self.risk_level,
        }


@dataclass(slots=True)
class PlanStep:
    index: int
    description: str
    tool_name: str | None = None
    requires_approval: bool = False
    max_retries: int = 0
    risk_level: str = "low"

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "description": self.description,
            "tool_name": self.tool_name,
            "requires_approval": self.requires_approval,
            "max_retries": self.max_retries,
            "risk_level": self.risk_level,
        }


@dataclass(slots=True)
class ExecutionTraceEntry:
    step: int
    status: str
    description: str
    tool: str | None = None
    output: Any = None
    error: str | None = None
    attempts: int = 0
    approved: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "step": self.step,
            "status": self.status,
            "description": self.description,
            "tool": self.tool,
            "output": self.output,
            "error": self.error,
            "attempts": self.attempts,
            "approved": self.approved,
            "metadata": self.metadata,
        }


@dataclass(slots=True)
class ExecutionResult:
    task: str
    plan: list[PlanStep]
    trace: list[ExecutionTraceEntry]
    state: dict[str, Any]
    evaluation: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "task": self.task,
            "plan": [step.to_dict() for step in self.plan],
            "trace": [entry.to_dict() for entry in self.trace],
            "state": self.state,
            "evaluation": self.evaluation,
        }
