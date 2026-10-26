from __future__ import annotations

import argparse
import json
from typing import Any

from .approval import ApprovalManager
from .models import ToolSpec
from .runtime import Runtime


def build_default_tools() -> list[ToolSpec]:
    def search_docs(context: dict[str, Any]) -> dict[str, Any]:
        task = context["task"]
        return {
            "status": "ok",
            "result": f"Found documentation relevant to: {task}",
        }

    def write_summary(context: dict[str, Any]) -> dict[str, Any]:
        task = context["task"]
        context["state"]["summary"] = f"Summary drafted for: {task}"
        return {
            "status": "ok",
            "result": f"Summary created for: {task}",
        }

    return [
        ToolSpec(
            name="search_docs",
            description="Search documents and reference material for the task",
            executor=search_docs,
        ),
        ToolSpec(
            name="write_summary",
            description="Create a structured summary after the task is understood",
            executor=write_summary,
        ),
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the agent reliability harness")
    parser.add_argument("task", nargs="?", default="Draft a summary for the project milestone")
    parser.add_argument("--approve-all", action="store_true", help="Auto-approve approval-gated tools")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    runtime = Runtime(
        approval_manager=ApprovalManager(approver=lambda tool, context: True) if args.approve_all else ApprovalManager(default_decision=False)
    )
    runtime.register_tools(build_default_tools())
    result = runtime.run(args.task)
    print(json.dumps(result.to_dict(), indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
