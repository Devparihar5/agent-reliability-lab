# Agent Reliability Lab

Agent Reliability Lab is an open-source agent runtime for building reliable, observable, and controllable AI systems on complex multi-step tasks.

It is designed around the idea that reliability is a runtime concern, not just a model prompt concern. The project helps you manage:

- planning and decomposition,
- tool selection and execution,
- retry and failure handling,
- human approval gates,
- durable execution state,
- evaluation and benchmarking.

This is not another chat UI. It is the orchestration layer behind dependable agent workflows.

## Why this exists

Most agent failures are not caused by a single bad model response. They happen when the runtime lacks:

- explicit task planning,
- structured tool metadata,
- retries with bounded policies,
- policy enforcement for risky actions,
- state persistence across steps,
- objective evaluation of the final outcome.

This library addresses those problems directly.

## Core runtime components

- Planner: decomposes a user request into a task plan.
- Tool registry: stores tool metadata and execution functions.
- Approval manager: blocks or requires approval for risky operations.
- State store: tracks execution state across plan steps.
- Retry policy: retries failures with controlled effort.
- Evaluator: scores each run for successful completion and process quality.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Quick start

```python
from agent_reliability_lab import Runtime, ToolSpec


def search_docs(context):
    task = context["task"]
    return {"result": f"Looked up docs for: {task}"}


def write_summary(context):
    task = context["task"]
    context["state"]["summary"] = f"Summary generated for {task}"
    return "summary-written"

runtime = Runtime()
runtime.register_tool(
    ToolSpec(
        name="search_docs",
        description="Search internal docs for reference material",
        executor=search_docs,
    )
)
runtime.register_tool(
    ToolSpec(
        name="write_summary",
        description="Write a report after research has been completed",
        executor=write_summary,
        requires_approval=False,
    )
)

result = runtime.run("Draft a launch report for the reliability harness")
print(result.evaluation)
print(result.trace)
```

## Approvals

Some tools may be risky, such as file writes, shell commands, or external API mutations. These tools can require approval before they run.

```python
from agent_reliability_lab import ApprovalManager, Runtime, ToolSpec


def shell_exec(context):
    return "ran command"


def always_approve(tool, context):
    return True

runtime = Runtime(
    approval_manager=ApprovalManager(approver=always_approve)
)
runtime.register_tool(
    ToolSpec(
        name="deploy",
        description="Deploy to production",
        executor=shell_exec,
        requires_approval=True,
        risk_level="high",
    )
)
```

## Architecture notes

The runtime is intentionally lightweight and composable:

- all core classes are Python dataclasses or regular classes,
- no heavy dependencies are required,
- you can swap in custom planners, state stores, or evaluators,
- the same harness can be used in CLI, service, or workflow environments.

## Roadmap

- SQLite and Redis-backed state stores
- durable event logs and execution traces
- stronger policy enforcement and compliance checks
- benchmark suites for reliability scoring
- API server and dashboards
- integration with external tool adapters

## License

MIT
