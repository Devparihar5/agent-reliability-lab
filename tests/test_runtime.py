from agent_reliability_lab.runtime import Runtime, ToolSpec


def search_docs(context):
    task = context["task"]
    return f"Found documentation for: {task}"


def write_summary(context):
    task = context["task"]
    context["state"]["summary"] = f"Summary drafted for {task}"
    return "Summary created"


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
        description="Create a written summary after gathering evidence",
        executor=write_summary,
    )
)

result = runtime.run("Draft a launch summary for the reliability harness")
print(result["evaluation"])
