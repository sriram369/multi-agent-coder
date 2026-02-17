"""LangGraph workflow definition for the multi-agent coding system."""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from langgraph.graph import END, START, StateGraph
from rich.console import Console

from agents.architect import ArchitectAgent
from agents.coder import CoderAgent
from agents.reviewer import ReviewerAgent
from agents.tester import TesterAgent
from orchestrator.state import AgentState
from tools.file_manager import clean_output_dir, write_files

load_dotenv()
console = Console()

# Instantiate agents once
architect = ArchitectAgent()
coder = CoderAgent()
reviewer = ReviewerAgent()
tester = TesterAgent()

MAX_REVIEW_CYCLES = int(os.getenv("MAX_REVIEW_CYCLES", "2"))


def architect_node(state: AgentState) -> dict:
    """Run the architect agent."""
    return architect.run(state)


def coder_node(state: AgentState) -> dict:
    """Run the coder agent."""
    return coder.run(state)


def reviewer_node(state: AgentState) -> dict:
    """Run the reviewer agent."""
    return reviewer.run(state)


def tester_node(state: AgentState) -> dict:
    """Run the tester agent."""
    return tester.run(state)


def file_writer_node(state: AgentState) -> dict:
    """Write all generated files (code + tests) to disk."""
    output_base = os.getenv("OUTPUT_DIR", "output")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = str(Path(output_base) / timestamp)

    console.print(f"\n[bold cyan]Writing files to {run_dir}/ ...[/bold cyan]")
    clean_output_dir(run_dir)

    all_files = {**state.files, **state.test_files}
    write_files(all_files, run_dir)

    console.print(f"[bold green]Wrote {len(all_files)} file(s) to disk.[/bold green]")

    return {
        "current_agent": "file_writer",
        "messages": [
            {
                "agent": "file_writer",
                "type": "write",
                "content": f"Wrote {len(all_files)} files to {run_dir}/",
            }
        ],
    }


def should_retry_or_test(state: AgentState) -> str:
    """Conditional edge: decide whether to loop back to coder or proceed to tester.

    Returns:
        "coder" if review found issues and we haven't hit the cycle limit,
        "tester" otherwise.
    """
    feedback_upper = state.review_feedback.upper()
    has_issues = "SEVERITY: MAJOR_ISSUES" in feedback_upper or "SEVERITY: MINOR_ISSUES" in feedback_upper

    if has_issues and state.review_count < MAX_REVIEW_CYCLES:
        console.print(
            f"[yellow]Review cycle {state.review_count}/{MAX_REVIEW_CYCLES} — "
            f"sending back to Coder for fixes.[/yellow]"
        )
        return "coder"

    if state.review_count >= MAX_REVIEW_CYCLES and has_issues:
        console.print(
            f"[yellow]Max review cycles ({MAX_REVIEW_CYCLES}) reached — "
            f"proceeding to testing regardless.[/yellow]"
        )

    return "tester"


def build_graph() -> StateGraph:
    """Build and compile the LangGraph workflow.

    Returns:
        A compiled StateGraph ready to invoke.
    """
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("architect", architect_node)
    graph.add_node("coder", coder_node)
    graph.add_node("reviewer", reviewer_node)
    graph.add_node("tester", tester_node)
    graph.add_node("file_writer", file_writer_node)

    # Add edges
    graph.add_edge(START, "architect")
    graph.add_edge("architect", "coder")
    graph.add_edge("coder", "reviewer")
    graph.add_conditional_edges(
        "reviewer",
        should_retry_or_test,
        {"coder": "coder", "tester": "tester"},
    )
    graph.add_edge("tester", "file_writer")
    graph.add_edge("file_writer", END)

    return graph.compile()
