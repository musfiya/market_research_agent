# Market Research Agent

A small multi-agent market research workflow built with LangGraph.

## Architecture

`mermaid
flowchart TD
    START([START]) --> Planner[Planner]
    Planner --> Researcher[Web Researcher]
    Researcher --> Analyst[Analyst]
    Analyst --> Writer[Writer]
    Writer --> Reviewer[Reviewer]
    Reviewer -->|Approved| END([END])
    Reviewer -->|Rejected, revision_count < 2| Writer
    Reviewer -->|Rejected, revision_count >= 2| Failure[Failure Handler]
    Failure --> END
`

## State Schema

The workflow uses a shared ResearchState object containing the original question, research plan, search queries, sources, research findings, analysis, draft report, reviewer feedback, review score, approval decision, revision count, final report, and workflow status.

## Agent Responsibilities

- **Planner:** Breaks the business question into focused research tasks and targeted search queries.
- **Web Researcher:** Searches the web, filters irrelevant results, removes duplicate URLs, and summarizes evidence.
- **Analyst:** Evaluates evidence, opportunities, risks, competition, and evidence gaps.
- **Writer:** Produces an executive-style market research report.
- **Reviewer:** Evaluates relevance, geographic accuracy, evidence quality, source credibility, reasoning, and recommendation quality.
- **Failure Handler:** Stops the workflow safely after two rejected reviews.

## Conditional Routing

The Reviewer creates a real decision point. Approved reports end the workflow. A rejected report with fewer than two revision attempts returns to the Writer. A report rejected twice enters the Failure Handler and the workflow stops.

## What Happens After Two Rejections?

The Failure Handler records the final reviewer feedback, marks the workflow as FAILED_REVIEW, explains that the report could not pass review after two attempts, and stops the workflow. This prevents an infinite revision loop.

## Failure Mode Found During Development

Testing showed that LLM-generated research can contain plausible-looking but poorly verified information. Testing also exposed geographic drift, where the model could answer for a different city than the original question.

The workflow was improved with targeted research queries, web search, source collection, geographic scope checks, evidence-gap detection, reviewer quality gates, and a maximum of two revision attempts.

A key design lesson was that an honest evidence gap should not automatically cause failure. A cautious recommendation that explicitly acknowledges missing evidence can still be useful.

## Example Run

Example question:

Should a premium coffee brand expand into Bangalore?

Workflow:

Planner -> Web Researcher -> Analyst -> Writer -> Reviewer

The Reviewer can approve the report, request a revision, or stop the workflow after repeated rejection.

## Project Structure

`	ext
market_research_agent/
|-- .env
|-- .gitignore
|-- README.md
|-- requirements.txt
|-- main.py
-- src/
    |-- __init__.py
    |-- state.py
    |-- agents.py
    -- graph.py
`

## Setup

Create a virtual environment, activate it, and install dependencies with pip install -r requirements.txt.

Create a .env file containing APINEX_API_KEY=your_api_key_here. The .env file is excluded from Git.

## Run

`powershell
python main.py
`

## Technologies

- Python
- LangGraph
- LangChain
- OpenAI-compatible LLM API
- DuckDuckGo Search
- python-dotenv

## Design Decisions

The system uses a typed shared state, a genuine conditional edge at the Reviewer, evidence before recommendation, and a bounded revision loop.

## Future Improvements

Possible improvements include better source credibility scoring, citation verification, structured numerical evidence extraction, persistent research memory, human approval, and stronger geographic validation.

## Key Learning

A multi-agent workflow is not just multiple LLM calls. The important engineering work is defining agent responsibilities, shared state, decision points, failure detection, and safe stopping behavior.

## License

Educational and demonstration project.