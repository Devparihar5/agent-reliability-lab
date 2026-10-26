from agent_reliability_lab import ApprovalManager, Runtime, ToolSpec


def deploy_to_prod(context):
    return {"status": "deployed"}


def always_approve(tool, context):
    return True


runtime = Runtime(approval_manager=ApprovalManager(approver=always_approve))
runtime.register_tool(
    ToolSpec(
        name="deploy",
        description="Deploy to production",
        executor=deploy_to_prod,
        requires_approval=True,
        risk_level="high",
    )
)

result = runtime.run("Ship the production update")
print(result.evaluation)
print(result.trace)
