from __future__ import annotations

from typing import Any, Callable

from .models import ToolSpec


class ApprovalManager:
    def __init__(
        self,
        approver: Callable[[ToolSpec, dict[str, Any]], bool] | None = None,
        default_decision: bool = False,
    ) -> None:
        self.approver = approver
        self.default_decision = default_decision

    def approve(self, tool: ToolSpec, context: dict[str, Any]) -> bool:
        if not tool.requires_approval:
            return True
        if self.approver is None:
            return self.default_decision
        return bool(self.approver(tool, context))
