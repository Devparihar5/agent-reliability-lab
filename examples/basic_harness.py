from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class ToolSpec:
    name: str
    description: str
    executor: Callable[[dict[str, Any]], Any]
    requires_approval: bool = False
    max_retries: int = 2
    risk_level: str = "low"

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "requires_approval": self.requires_approval,
            "max_retries": self.max_retries,
            "risk_level": self.risk_level,
        }


@dataclass
class PlanStep:
    index: int
    description: str
    tool_name: str | None = None
    requires_approval: bool = False
    max_retries: int = 2

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "description": self.description,
            "tool_name": self.tool_name,
            "requires_approval": self.requires_approval,
            "max_retries": self.max_retries,
        }


class StateStore:
    def __init__(self) -> None:
        self.state: dict[str, Any] = {}

    def set(self, key: str, value: Any) -> None:
        self.state[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self.state.get(key, default)

    def snapshot(self) -> dict[str, Any]:
        return dict(self.state)

    def reset(self) -> None:
        self.state.clear()


class ApprovalManager:
    def __init__(self, approver: Callable[[ToolSpec, dict[str, Any]], bool] | None = None) -> None:
        self.approver = approver

    def approve(self, tool: ToolSpec, context: dict[str, Any]) -> bool:
        if not tool.requires_approval:
            return True
        if self.approver is None:
            return False
        return bool(self.approver(tool, context))


class Planner:
    def __init__(self, fallback_description: str = "Reason through the task and gather evidence") -> None:
        self.fallback_description = fallback_description

    def create_plan(self, task: str, tools: list[ToolSpec]) -> list[PlanStep]:
        task_lower = task.lower()
        keyword_tokens = [token for token in task_lower.replace("-", " ").split() if token]

        if not tools:
            return [
                PlanStep(
                    index=0,
                    description=self.fallback_description,
                    tool_name=None,
                    requires_approval=False,
                    max_retries=0,
                )
            ]

        ranked = []
        for tool in tools:
            tool_text = (tool.name + " " + tool.description).lower()
            score = sum(1 for token in keyword_tokens if token in tool_text)
            ranked.append((score, tool))

        ranked.sort(key=lambda item: item[0], reverse=True)
        selected = [tool for score, tool in ranked if score > 0]
        if not selected:
            selected = tools[: min(2, len(tools))]

        plan: list[PlanStep] = []
        for index, tool in enumerate(selected):
            plan.append(
                PlanStep(
                    index=index,
                    description=f"Execute {tool.name}: {tool.description}",
                    tool_name=tool.name,
                    requires_approval=tool.requires_approval,
                    max_retries=tool.max_retries,
                )
            )

        return plan


class Evaluator:
    def evaluate(self, task: str, trace: list[dict[str, Any]], state: dict[str, Any]) -> dict[str, Any]:
        successful_steps = sum(1 for item in trace if item.get("status") == "success")
        failed_steps = sum(1 for item in trace if item.get("status") == "failed")
        blocked_steps = sum(1 for item in trace if item.get("status") == "blocked")

        score = max(0.0, (successful_steps / max(1, successful_steps + failed_steps + blocked_steps)) * 100.0)

        return {
            "task": task,
            "passed": failed_steps == 0 and blocked_steps == 0,
            "score": round(score, 2),
            "successful_steps": successful_steps,
            "failed_steps": failed_steps,
            "blocked_steps": blocked_steps,
            "state_summary": state,
        }


@dataclass
class ExecutionResult:
    task: str
    plan: list[PlanStep] = field(default_factory=list)
    trace: list[dict[str, Any]] = field(default_factory=list)
    state: dict[str, Any] = field(default_factory=dict)
    evaluation: dict[str, Any] = field(default_factory=dict)


class Runtime:
    def __init__(
        self,
        planner: Planner | None = None,
        approval_manager: ApprovalManager | None = None,
        evaluator: Evaluator | None = None,
        state_store: StateStore | None = None,
    ) -> None:
        self.registry: dict[str, ToolSpec] = {}
        self.planner = planner or Planner()
        self.approval_manager = approval_manager or ApprovalManager()
        self.evaluator = evaluator or Evaluator()
        self.state_store = state_store or StateStore()

    def register_tool(self, tool: ToolSpec) -> None:
        self.registry[tool.name] = tool

    def get_tool(self, name: str) -> ToolSpec | None:
        return self.registry.get(name)

    def run(self, task: str) -> dict[str, Any]:
        self.state_store.reset()
        self.state_store.set("task", task)

        plan = self.planner.create_plan(task, list(self.registry.values()))
        self.state_store.set("plan", [step.to_dict() for step in plan])

        trace: list[dict[str, Any]] = []

        for step in plan:
            if step.tool_name is None:
                trace.append({
                    "step": step.index,
                    "status": "success",
                    "description": step.description,
                    "output": "No tool required; task analyzed.",
                })
                continue

            tool = self.get_tool(step.tool_name)
            if tool is None:
                trace.append({
                    "step": step.index,
                    "status": "failed",
                    "description": step.description,
                    "error": f"Tool '{step.tool_name}' is not registered.",
                })
                continue

            context = {
                "task": task,
                "step": step.to_dict(),
                "state": self.state_store.snapshot(),
            }

            if tool.requires_approval and not self.approval_manager.approve(tool, context):
                trace.append({
                    "step": step.index,
                    "status": "blocked",
                    "description": step.description,
                    "tool": tool.name,
                    "reason": "Approval required.",
                })
                continue

            attempts = 0
            while attempts <= step.max_retries:
                try:
                    output = tool.executor(context)
                    self.state_store.set(f"step_{step.index}_output", output)
                    trace.append({
                        "step": step.index,
                        "status": "success",
                        "description": step.description,
                        "tool": tool.name,
                        "output": output,
                    })
                    break
                except Exception as exc:  # pragma: no cover - behavior is simple and tested elsewhere
                    attempts += 1
                    if attempts > step.max_retries:
                        trace.append({
                            "step": step.index,
                            "status": "failed",
                            "description": step.description,
                            "tool": tool.name,
                            "error": str(exc),
                            "attempts": attempts,
                        })
                        break
                    context["last_error"] = str(exc)

        evaluation = self.evaluator.evaluate(task, trace, self.state_store.snapshot())
        self.state_store.set("trace", trace)
        self.state_store.set("evaluation", evaluation)

        return {
            "task": task,
            "plan": [step.to_dict() for step in plan],
            "trace": trace,
            "state": self.state_store.snapshot(),
            "evaluation": evaluation,
        }
