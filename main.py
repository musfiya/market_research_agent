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

    result = graph.invoke(initial_state)

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
