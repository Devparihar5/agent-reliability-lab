from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from .models import PlanStep, ToolSpec


class Planner:
    def __init__(self, fallback_description: str = "Reason through the task and form a plan") -> None:
        self.fallback_description = fallback_description

    def build_plan(self, task: str, tools: Sequence[ToolSpec], state: dict[str, Any] | None = None) -> list[PlanStep]:
        task_text = task.lower()
        tokens = [token for token in task_text.replace("-", " ").split() if token]

        if not tools:
            return [
                PlanStep(
                    index=0,
                    description=self.fallback_description,
                    tool_name=None,
                    requires_approval=False,
                    max_retries=0,
                    risk_level="low",
                )
            ]

        ranked = []
        for tool in tools:
            tool_text = f"{tool.name} {tool.description}".lower()
            score = sum(1 for token in tokens if token in tool_text)
            ranked.append((score, tool))

        ranked.sort(key=lambda item: item[0], reverse=True)
        selected = [tool for score, tool in ranked if score > 0]
        if not selected:
            selected = list(tools)[: min(2, len(tools))]

        plan: list[PlanStep] = []
        for index, tool in enumerate(selected):
            plan.append(
                PlanStep(
                    index=index,
                    description=f"Run {tool.name}: {tool.description}",
                    tool_name=tool.name,
                    requires_approval=tool.requires_approval,
                    max_retries=max(0, tool.max_retries),
                    risk_level=tool.risk_level,
                )
            )

        return plan
