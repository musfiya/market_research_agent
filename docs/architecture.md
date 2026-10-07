# Market Research Agent - Architecture

## Overview

This project implements a bounded multi-agent market research workflow using LangGraph. Each agent performs a specific stage of the research process and communicates through a shared typed state.

## Architecture Diagram

`mermaid
flowchart TD
    START([START]) --> Planner[Planner]
    Planner --> Researcher[Web Researcher]
    Researcher --> Analyst[Analyst]
    Analyst --> Writer[Writer]
    Writer --> Reviewer[Reviewer]

    Reviewer -->|Approved| END([END])
    Reviewer -->|Rejected and revision_count < 2| Writer
    Reviewer -->|Rejected and revision_count >= 2| Failure[Failure Handler]

    Failure --> END
`

## State Flow

`	ext
Business Question
       |
       v
+--------------+
|    Planner   |
+--------------+
       |
       | research_plan + search_queries
       v
+-------------------+
|  Web Researcher   |
+-------------------+
       |
       | sources + research_data
       v
+--------------+
|   Analyst    |
+--------------+
       |
       | analysis
       v
+--------------+
|    Writer    |
+--------------+
       |
       | draft_report
       v
+--------------+
|   Reviewer   |
+--------------+
       |
       +---------------------> APPROVED -> END
       |
       +--> REJECTED, revision_count < 2
       |          |
       |          v
       |        Writer
       |
       +--> REJECTED, revision_count >= 2
                  |
                  v
           Failure Handler
                  |
                  v
                 END
`

## Nodes

### 1. Planner

The Planner receives the original business question and creates a focused research plan and targeted web-search queries.

### 2. Web Researcher

The Researcher executes the search queries, collects web sources, removes duplicate URLs, filters obvious irrelevant results, and summarizes the evidence.

### 3. Analyst

The Analyst interprets the collected evidence and identifies market opportunities, risks, competitors, implications, and evidence gaps.

### 4. Writer

The Writer converts the research and analysis into an executive-style market research report.

### 5. Reviewer

The Reviewer evaluates whether the report is relevant, evidence-based, geographically correct, logically supported, and professionally written.

### 6. Failure Handler

The Failure Handler is reached when the report has been rejected twice. It records the final feedback and stops the workflow safely.

## Conditional Edge

The Reviewer is the main decision point in the graph.

`	ext
Reviewer
   |
   +-- approved ----------------------> END
   |
   +-- rejected + revision_count < 2 --> Writer
   |
   +-- rejected + revision_count >= 2 -> Failure Handler -> END
`

This is a real conditional edge because the next node depends on the review result and the number of previous revision attempts.

## Two-Rejection Failure Behavior

The revision loop is intentionally bounded.

If the Reviewer rejects the report:

1. 
evision_count is incremented.
2. The Writer receives the reviewer feedback.
3. The Writer produces a revised report.
4. The Reviewer evaluates the revised report again.

After the second rejection, the graph does **not** return to the Writer. Instead, the conditional router sends execution to the Failure Handler.

The Failure Handler sets the workflow status to FAILED_REVIEW and returns the final reviewer feedback. This prevents an infinite revision loop.

## Failure Mode Discovered During Testing

A major failure mode identified during development was that an LLM could produce plausible-looking market statistics without sufficient evidence.

Testing also revealed geographic drift. For example, a question about one city could result in a report focused on another city.

The workflow was improved by adding:

- Targeted search queries
- Web-source collection
- Duplicate URL removal
- Geographic scope checks
- Evidence-gap detection
- Reviewer quality checks
- A bounded two-revision loop

The final quality gate does not automatically reject honest uncertainty. If evidence is insufficient, the system can produce a cautious recommendation that explicitly acknowledges the gap instead of inventing certainty.

## Design Principle

The central design principle is **evidence before recommendation**.

The Writer does not receive only the original question. It receives the Researcher's evidence and the Analyst's interpretation. The Reviewer then checks whether the final recommendation is supported by that evidence.

This creates a traceable flow:

`	ext
Question
   -> Research Plan
   -> Web Evidence
   -> Analysis
   -> Report
   -> Review Decision
`

## Technology

- Python
- LangGraph
- LangChain
- OpenAI-compatible LLM API
- DuckDuckGo Search
- python-dotenv
