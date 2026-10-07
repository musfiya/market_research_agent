from src.graph import graph


def main():
    print("=" * 70)
    print("BUSINESS MARKET RESEARCH AGENT")
    print("=" * 70)

    question = input("\nEnter your business question:\n> ").strip()

    if not question:
        print("Please enter a business question.")
        return

    initial_state = {
        "question": question,
        "research_plan": [],
        "search_queries": [],
        "sources": [],
        "research_data": [],
        "analysis": "",
        "draft_report": "",
        "reviewer_feedback": "",
        "review_score": 0,
        "approved": False,
        "revision_count": 0,
        "final_report": "",
        "status": "RUNNING",
    }

    print("\nRunning multi-agent workflow...")
    print("Planner -> Web Researcher -> Analyst -> Writer -> Reviewer\n")

    final_state = initial_state.copy()

    node_names = {
        "planner": "Planner",
        "researcher": "Web Researcher",
        "analyst": "Analyst",
        "writer": "Writer",
        "reviewer": "Reviewer",
        "failure_handler": "Failure Handler",
    }

    for update in graph.stream(initial_state):
        for node, values in update.items():
            final_state.update(values)

            print(f"✓ {node_names.get(node, node)} completed")

            if node == "reviewer":
                if values.get("approved"):
                    print("  → Review approved")
                elif values.get("revision_count", 0) < 2:
                    print("  → Review rejected; sending back to Writer")
                else:
                    print("  → Review rejected twice; stopping")

    result = final_state

    print("=" * 70)
    print("FINAL RESULT")
    print("=" * 70)

    if result["status"] == "FAILED_REVIEW":
        print("\nSTATUS: FAILED AFTER TWO REVIEWS\n")
        print(result["final_report"])
    else:
        print("\nSTATUS: APPROVED\n")
        print(result["draft_report"])

    print("\n" + "-" * 70)
    print(f"Web sources collected: {len(result['sources'])}")
    print(f"Review score: {result['review_score']}/10")
    print(f"Revision attempts: {result['revision_count']}")
    print("-" * 70)


if __name__ == "__main__":
    main()
