from __future__ import annotations

from typing import Any

from .approval import ApprovalManager
from .evaluator import Evaluator
from .models import ExecutionResult, ExecutionTraceEntry, PlanStep, ToolSpec
from .planner import Planner
from .state import InMemoryStateStore


class Runtime:
    def __init__(
        self,
        planner: Planner | None = None,
        approval_manager: ApprovalManager | None = None,
        evaluator: Evaluator | None = None,
        state_store: InMemoryStateStore | None = None,
    ) -> None:
        self.registry: dict[str, ToolSpec] = {}
        self.planner = planner or Planner()
        self.approval_manager = approval_manager or ApprovalManager(default_decision=False)
        self.evaluator = evaluator or Evaluator()
        self.state_store = state_store or InMemoryStateStore()

    def register_tool(self, tool: ToolSpec) -> None:
        self.registry[tool.name] = tool

    def register_tools(self, tools: list[ToolSpec]) -> None:
        for tool in tools:
            self.register_tool(tool)

    def get_tool(self, name: str) -> ToolSpec | None:
        return self.registry.get(name)

    def run(self, task: str, *, context: dict[str, Any] | None = None) -> ExecutionResult:
        self.state_store.reset()
        base_context = {"task": task, "state": self.state_store.snapshot()}
        if context:
            base_context.update(context)
        self.state_store.set("task", task)
        self.state_store.set("context", base_context)

        plan = self.planner.build_plan(task, list(self.registry.values()), self.state_store.snapshot())
        self.state_store.set("plan", [step.to_dict() for step in plan])

        trace: list[ExecutionTraceEntry] = []

        for step in plan:
            if step.tool_name is None:
                trace.append(
                    ExecutionTraceEntry(
                        step=step.index,
                        status="success",
                        description=step.description,
                        approved=True,
                        output="No tool required; plan created.",
                    )
                )
                continue

            tool = self.get_tool(step.tool_name)
            if tool is None:
                trace.append(
                    ExecutionTraceEntry(
                        step=step.index,
                        status="failed",
                        description=step.description,
                        tool=step.tool_name,
                        error=f"Tool '{step.tool_name}' is not registered.",
                        approved=True,
                    )
                )
                continue

            execution_context = {
                "task": task,
                "step": step.to_dict(),
                "state": self.state_store.snapshot(),
                "context": dict(base_context),
            }

            approved = self.approval_manager.approve(tool, execution_context)
            if tool.requires_approval and not approved:
                trace.append(
                    ExecutionTraceEntry(
                        step=step.index,
                        status="blocked",
                        description=step.description,
                        tool=tool.name,
                        approved=False,
                        metadata={"reason": "Approval required."},
                    )
                )
                continue

            attempts = 0
            while attempts <= max(0, step.max_retries):
                try:
                    output = tool.executor(execution_context)
                    self.state_store.set(f"step_{step.index}_output", output)
                    trace.append(
                        ExecutionTraceEntry(
                            step=step.index,
                            status="success",
                            description=step.description,
                            tool=tool.name,
                            output=output,
                            attempts=attempts + 1,
                            approved=True,
                        )
                    )
                    break
                except Exception as exc:  # pragma: no cover - actual behavior is exercised by tests
                    attempts += 1
                    if attempts > max(0, step.max_retries):
                        trace.append(
                            ExecutionTraceEntry(
                                step=step.index,
                                status="failed",
                                description=step.description,
                                tool=tool.name,
                                error=str(exc),
                                attempts=attempts,
                                approved=True,
                            )
                        )
                        break
                    execution_context["last_error"] = str(exc)

        evaluation = self.evaluator.evaluate(task, [entry.to_dict() for entry in trace], self.state_store.snapshot())
        self.state_store.set("trace", [entry.to_dict() for entry in trace])
        self.state_store.set("evaluation", evaluation)

        result = ExecutionResult(
            task=task,
            plan=plan,
            trace=trace,
            state=self.state_store.snapshot(),
            evaluation=evaluation,
        )
        return result
