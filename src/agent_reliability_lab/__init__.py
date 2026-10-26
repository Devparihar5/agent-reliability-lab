from agent_reliability_lab import ApprovalManager, Planner, Runtime, ToolSpec


def test_planner_selects_relevant_tools():
    tools = [
        ToolSpec("search_docs", "Search documentation for the API", lambda ctx: "docs"),
        ToolSpec("deploy", "Deploy the service to production", lambda ctx: "deployed", requires_approval=True),
    ]

    plan = Planner().build_plan("search docs for the API", tools, {})

    assert isinstance(plan, list)
    assert plan[0].tool_name == "search_docs"


def test_runtime_executes_successfully():
    def search_docs(context):
        return {"result": f"Search completed for {context['task']}"}

    runtime = Runtime()
    runtime.register_tool(
        ToolSpec(
            name="search_docs",
            description="Search documentation",
            executor=search_docs,
        )
    )

    result = runtime.run("Compile release notes")

    assert result.evaluation["passed"] is True
    assert result.trace[0].status == "success"


def test_runtime_blocks_approval_required_tools():
    def deploy(context):
        return {"status": "deployed"}

    runtime = Runtime(approval_manager=ApprovalManager(default_decision=False))
    runtime.register_tool(
        ToolSpec(
            name="deploy",
            description="Deploy to production",
            executor=deploy,
            requires_approval=True,
            risk_level="high",
        )
    )

    result = runtime.run("Deploy to prod")

    assert result.evaluation["blocked_steps"] == 1
    assert result.trace[0].status == "blocked"


def test_runtime_retries_with_policy():
    attempts = {"count": 0}

    def flaky_tool(context):
        attempts["count"] += 1
        if attempts["count"] < 2:
            raise RuntimeError("temporary failure")
        return {"status": "ok"}

    runtime = Runtime()
    runtime.register_tool(
        ToolSpec(
            name="flaky_tool",
            description="A flaky tool",
            executor=flaky_tool,
            max_retries=2,
        )
    )

    result = runtime.run("Check flaky tool")

    assert result.evaluation["successful_steps"] == 1
    assert attempts["count"] == 2
