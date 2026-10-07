import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from ddgs import DDGS

from src.state import ResearchState


load_dotenv()


llm = ChatOpenAI(
    model="free/gpt-6-luna",
    api_key=os.getenv("APINEX_API_KEY"),
    base_url="https://api.apinex.bond/v1",
    temperature=0.2,
)


def planner(state: ResearchState) -> dict:
    """Create research tasks and targeted search queries."""

    prompt = f"""
You are a professional market research planner.

ORIGINAL BUSINESS QUESTION:
{state["question"]}

Create exactly 4 research areas.

The research MUST remain focused on the location in the original question.

For each research area provide:
TASK: <research task>
QUERY: <short Google-style search query>

Good search queries should look like:

premium coffee market Hyderabad
specialty coffee Hyderabad competition
Hyderabad cafe consumer trends
Hyderabad commercial retail rent coffee shops

Do NOT put the entire business question into the search query.

Return exactly 4 TASK/QUERY pairs.
"""

    response = llm.invoke(prompt)

    tasks = []
    queries = []

    current_task = None

    for line in response.content.splitlines():
        line = line.strip()

        if line.upper().startswith("TASK:"):
            current_task = line.split(":", 1)[1].strip()
            tasks.append(current_task)

        elif line.upper().startswith("QUERY:"):
            query = line.split(":", 1)[1].strip()
            queries.append(query)

    # Safety fallback if the model does not follow the requested format.
    if len(tasks) != 4:
        tasks = [
            f"Market demand for {state['question']}",
            f"Competitors relevant to {state['question']}",
            f"Customers and pricing relevant to {state['question']}",
            f"Risks and opportunities relevant to {state['question']}",
        ]

    if len(queries) != 4:
        queries = [
            f"premium coffee market Hyderabad",
            f"premium coffee competitors Hyderabad",
            f"coffee consumer trends Hyderabad",
            f"coffee shop risks opportunities Hyderabad",
        ]

    return {
        "research_plan": tasks[:4],
        "search_queries": queries[:4],
    }


def researcher(state: ResearchState) -> dict:
    """Perform targeted web searches and collect useful sources."""

    sources = []

    for query in state["search_queries"]:

        try:
            results = DDGS().text(
                query,
                region="in-en",
                safesearch="moderate",
                max_results=5,
            )

            for result in results:

                title = result.get("title", "")
                url = result.get("href", "")
                snippet = result.get("body", "")

                combined = f"{title} {snippet}".lower()

                # Reject obvious irrelevant technical/data artifacts.
                irrelevant_terms = [
                    "password generator",
                    "word frequency",
                    "ocr dictionary",
                    "javascript gist",
                    "tesseract",
                    "package documentation",
                    "source code",
                ]

                if any(term in combined for term in irrelevant_terms):
                    continue

                if not title or not url:
                    continue

                sources.append(
                    {
                        "query": query,
                        "title": title,
                        "url": url,
                        "snippet": snippet,
                    }
                )

        except Exception as exc:
            print(f"Search warning for query {query}: {exc}")

    # Remove duplicate URLs.
    unique_sources = []
    seen_urls = set()

    for source in sources:
        if source["url"] not in seen_urls:
            seen_urls.add(source["url"])
            unique_sources.append(source)

    source_text = "\n\n".join(
        [
            f"""
Search query: {source["query"]}
Title: {source["title"]}
URL: {source["url"]}
Snippet: {source["snippet"]}
"""
            for source in unique_sources
        ]
    )

    if not source_text:
        source_text = "No relevant web sources were retrieved."

    prompt = f"""
You are a professional market research analyst.

ORIGINAL BUSINESS QUESTION:
{state["question"]}

WEB SOURCES RETRIEVED:
{source_text}

Create a research summary that answers ONLY the original business question.

STRICT RULES:

1. Stay focused on the exact geographic location in the question.
2. Do not substitute another city.
3. Do not invent statistics.
4. Do not invent facts.
5. Do not treat an irrelevant source as evidence.
6. If evidence is insufficient, clearly state that.
7. Associate important claims with their source URLs.
8. Distinguish facts from interpretation.

Return:
- Key findings
- Evidence gaps
- Source URLs
"""

    response = llm.invoke(prompt)

    return {
        "sources": unique_sources,
        "research_data": [response.content],
    }


def analyst(state: ResearchState) -> dict:
    """Analyze the research while preserving scope and evidence."""

    research = "\n".join(state["research_data"])

    prompt = f"""
You are a business analyst.

ORIGINAL BUSINESS QUESTION:
{state["question"]}

RESEARCH:
{research}

SOURCE COUNT:
{len(state["sources"])}

Analyze the evidence.

Before making a recommendation:
- Verify that the research addresses the requested location.
- Do not rely on unrelated sources.
- Identify important evidence gaps.
- Do not invent missing data.

Identify:
- Key opportunities
- Key risks
- Competitive considerations
- Customer considerations
- Evidence gaps
- Overall recommendation

Return a concise analytical summary.
"""

    response = llm.invoke(prompt)

    return {
        "analysis": response.content
    }


def writer(state: ResearchState) -> dict:
    """Write or revise the final business report."""

    source_list = "\n".join(
        f"- {source['title']} - {source['url']}"
        for source in state["sources"]
    )

    revision_context = ""

    if state["reviewer_feedback"]:
        revision_context = f"""
The previous draft was rejected.

Reviewer feedback:
{state["reviewer_feedback"]}

Revise the report specifically based on this feedback.
"""

    prompt = f"""
You are a professional business report writer.

ORIGINAL BUSINESS QUESTION:
{state["question"]}

RESEARCH:
{chr(10).join(state["research_data"])}

ANALYSIS:
{state["analysis"]}

AVAILABLE SOURCES:
{source_list}

REVISION NUMBER:
{state["revision_count"]}

{revision_context}

Write a concise executive-style business report.

Include:
1. Executive Summary
2. Market Opportunity
3. Competitive Landscape
4. Key Risks
5. Recommendation
6. Sources

CRITICAL:
- Answer the exact original business question.
- Keep the requested geography correct.
- Never invent statistics.
- Never present unsupported claims as facts.
- Mention important evidence gaps.
- Preserve source URLs.
- Do not mention the internal agent workflow.
"""

    response = llm.invoke(prompt)

    return {
        "draft_report": response.content,
        "final_report": response.content,
        "status": "REPORT_READY",
    }


def reviewer(state: ResearchState) -> dict:
    """Review the report using an LLM plus deterministic quality checks."""

    source_list = "\n".join(
        f"- {source['title']} | {source['url']}"
        for source in state["sources"]
    )

    prompt = f"""
You are a strict senior market research reviewer.

ORIGINAL BUSINESS QUESTION:
{state["question"]}

RESEARCH:
{chr(10).join(state["research_data"])}

ANALYSIS:
{state["analysis"]}

REPORT:
{state["draft_report"]}

SOURCES:
{source_list}

Evaluate:

1. Does the report answer the exact original question?
2. Is the geographic market correct?
3. Are important factual claims supported?
4. Are numerical claims supported?
5. Are sources relevant and credible?
6. Does the recommendation follow from the evidence?
7. Are evidence gaps honestly acknowledged?
8. Is the reasoning logical?
9. Is the report professionally written?

Be strict. A polished report is not automatically a good research report.

Return exactly:

SCORE: <number>
DECISION: APPROVED or REJECTED
FEEDBACK: <specific feedback>
"""

    response = llm.invoke(prompt)
    text = response.content.strip()

    score = 0
    approved = False
    feedback = text

    for line in text.splitlines():
        if line.upper().startswith("SCORE:"):
            try:
                score = int(line.split(":", 1)[1].strip())
            except ValueError:
                score = 0

        elif line.upper().startswith("DECISION:"):
            decision = line.split(":", 1)[1].strip().upper()
            approved = decision == "APPROVED"

        elif line.upper().startswith("FEEDBACK:"):
            feedback = line.split(":", 1)[1].strip()

    # ---------------------------------------------------------
    # Deterministic quality gate
    # ---------------------------------------------------------
    report_lower = state["draft_report"].lower()
    analysis_lower = state["analysis"].lower()

    quality_issues = []

    # A report may honestly acknowledge missing evidence.
    # That is NOT automatically a failure.
    #
    # We reject only when the report makes a strong recommendation
    # despite those gaps, or when there are integrity problems.

    strong_commitment_terms = [
        "definitely expand",
        "strongly recommend expansion",
        "immediately expand",
        "proceed with full-scale expansion",
        "commit to expansion",
        "highly profitable",
        "guaranteed",
    ]

    evidence_gap_terms = [
        "insufficient data",
        "insufficient evidence",
        "evidence gap",
        "missing data",
        "not available",
        "no data",
        "cannot be determined",
        "unproven",
        "zero visibility",
    ]

    has_evidence_gap = any(
        term in report_lower or term in analysis_lower
        for term in evidence_gap_terms
    )

    strong_commitment = any(
        term in report_lower
        for term in strong_commitment_terms
    )

    # Honest evidence gap + cautious recommendation is acceptable.
    if has_evidence_gap and strong_commitment:
        quality_issues.append(
            "The report acknowledges major evidence gaps but still makes a strong expansion commitment."
        )

    # Too few sources can still be acceptable if the report clearly
    # limits its recommendation, but extremely small source sets are risky.
    if len(state["sources"]) < 3:
        quality_issues.append(
            "Too few web sources were collected to support a meaningful assessment."
        )

    # Failed searches are warnings, not automatic failures.
    # The researcher is allowed to continue with partial evidence.

    # Check for obvious temporal integrity problems.
    temporal_conflict_terms = [
        "temporal impossibility",
        "future data",
        "future report",
        "date conflict",
        "dated incorrectly",
        "publication date conflict",
    ]

    if any(term in report_lower for term in temporal_conflict_terms):
        quality_issues.append(
            "The report contains a possible temporal inconsistency in its evidence."
        )

    # Apply deterministic rejection.
    if quality_issues:
        approved = False

        deterministic_feedback = "\n".join(
            f"- {issue}" for issue in quality_issues
        )

        feedback = (
            "QUALITY GATE REJECTION:\n"
            + deterministic_feedback
            + "\n\nLLM REVIEW:\n"
            + feedback
        )

    new_revision_count = state["revision_count"]


    if not approved:
        new_revision_count += 1

    return {
        "reviewer_feedback": feedback,
        "review_score": score,
        "approved": approved,
        "revision_count": new_revision_count,
        "status": "APPROVED" if approved else "REJECTED",
    }

def failure_handler(state: ResearchState) -> dict:
    """Handle reports rejected twice."""

    message = f"""
The report could not pass review after two revision attempts.

Final reviewer feedback:
{state["reviewer_feedback"]}

The workflow has stopped safely instead of continuing indefinitely.
"""

    return {
        "final_report": message,
        "status": "FAILED_REVIEW",
    }





