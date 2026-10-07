from langgraph.graph import StateGraph, START, END

from src.state import ResearchState
from src.agents import (
    planner,
    researcher,
    analyst,
    writer,
    reviewer,
    failure_handler,
)


def review_router(state: ResearchState) -> str:
    """
    Decide what happens after the reviewer evaluates the report.
    """

    if state["approved"]:
        return "approved"

    if state["revision_count"] < 2:
        return "revise"

    return "failed"


def build_graph():
    workflow = StateGraph(ResearchState)

    # Add agent nodes
    workflow.add_node("planner", planner)
    workflow.add_node("researcher", researcher)
    workflow.add_node("analyst", analyst)
    workflow.add_node("writer", writer)
    workflow.add_node("reviewer", reviewer)
    workflow.add_node("failure_handler", failure_handler)

    # Main workflow
    workflow.add_edge(START, "planner")
    workflow.add_edge("planner", "researcher")
    workflow.add_edge("researcher", "analyst")
    workflow.add_edge("analyst", "writer")
    workflow.add_edge("writer", "reviewer")

    # Conditional reviewer decision
    workflow.add_conditional_edges(
        "reviewer",
        review_router,
        {
            "approved": END,
            "revise": "writer",
            "failed": "failure_handler",
        },
    )

    # Failure path
    workflow.add_edge("failure_handler", END)

    return workflow.compile()


graph = build_graph()
