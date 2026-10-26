from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class EvaluationResult:
    task: str
    passed: bool
    score: float
    successful_steps: int
    failed_steps: int
    blocked_steps: int
    state_summary: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "task": self.task,
            "passed": self.passed,
            "score": self.score,
            "successful_steps": self.successful_steps,
            "failed_steps": self.failed_steps,
            "blocked_steps": self.blocked_steps,
            "state_summary": self.state_summary,
        }


class Evaluator:
    def evaluate(self, task: str, trace: list[dict[str, Any]], state: dict[str, Any]) -> dict[str, Any]:
        successful_steps = sum(1 for item in trace if item.get("status") == "success")
        failed_steps = sum(1 for item in trace if item.get("status") == "failed")
        blocked_steps = sum(1 for item in trace if item.get("status") == "blocked")

        total = max(1, successful_steps + failed_steps + blocked_steps)
        score = (successful_steps / total) * 100.0

        result = EvaluationResult(
            task=task,
            passed=(failed_steps == 0 and blocked_steps == 0),
            score=round(score, 2),
            successful_steps=successful_steps,
            failed_steps=failed_steps,
            blocked_steps=blocked_steps,
            state_summary=dict(state),
        )
        return result.to_dict()
