from agent_reliability_lab import Runtime, ToolSpec


def search_docs(context):
    task = context["task"]
    return {"result": f"Found docs for: {task}"}


def write_summary(context):
    task = context["task"]
    context["state"]["summary"] = f"Summary generated for {task}"
    return {"result": f"Summary written for {task}"}


runtime = Runtime()
runtime.register_tool(
    ToolSpec(
        name="search_docs",
        description="Search internal docs and reference materials",
        executor=search_docs,
    )
)
runtime.register_tool(
    ToolSpec(
        name="write_summary",
        description="Create a summary after gathering evidence",
        executor=write_summary,
    )
)

result = runtime.run("Draft a launch summary for the reliability harness")
print(result.evaluation)
print(result.state)
