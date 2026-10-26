# Agent Reliability Lab

Agent Reliability Lab is an open-source runtime for building more dependable AI agents on multi-step tasks. It provides a small but practical harness for: planning, tool execution, retries, approvals, durable state, and evaluation.

The goal is not to build a chat UI. Instead, it focuses on the runtime that makes agents more controllable and observable in real workflows.

## Why this exists

AI agents often fail on long-running tasks because they:

- lose track of the current objective,
- execute tools without guardrails,
- retry poorly when tools fail,
- lack approval checkpoints for risky actions,
- have no structured execution state,
- are hard to evaluate objectively.

This project treats those as first-class concerns.

## Core concepts

- Planner: turns a user task into an actionable execution plan.
- Tool registry: stores tools with metadata, retry settings, and risk levels.
- Approval gate: requires explicit approval for actions marked as risky.
- State store: captures intermediate results for durable execution.
- Retry loop: reruns failed tool calls with bounded retry policies.
- Evaluator: scores the final execution based on the task, outputs, and state.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Example usage

```python
from agent_reliability_lab.runtime import Runtime
from agent_reliability_lab.tools import ToolSpec


def search_docs(context):
    task = context["task"]
    return f"Found documentation for: {task}"


def write_report(context):
    task = context["task"]
    context["state"]["report"] = f"Report generated for {task}"
    return "Report written"

runtime = Runtime()
runtime.register_tool(
    ToolSpec(
        name="search_docs",
        description="Search internal docs and reference material",
        executor=search_docs,
    )
)
runtime.register_tool(
    ToolSpec(
        name="write_report",
        description="Create a report from completed research",
        executor=write_report,
        requires_approval=False,
    )
)

result = runtime.run("Write a migration report for the API")
print(result["evaluation"]) 
```

## Repository layout

- `src/agent_reliability_lab/` — runtime implementation
- `examples/` — sample usage and harness setup
- `tests/` — unit tests for core behavior

## Roadmap

- durable state backends (SQLite, Redis, Postgres)
- structured tool schemas and validation
- plan re-planning loops
- event streaming and observability
- benchmark suites for agent reliability
- UI dashboard for execution traces

## License

MIT
