"""CLI entry point for the multi-agent collaborative coding system."""

from __future__ import annotations

import sys
import time

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from orchestrator.graph import build_graph
from orchestrator.state import AgentState

load_dotenv()
console = Console()

# Cost per million tokens for Claude Sonnet 4 (approximate)
INPUT_COST_PER_M = 3.00
OUTPUT_COST_PER_M = 15.00


def display_banner() -> None:
    """Display the application banner."""
    banner = (
        "[bold cyan]Multi-Agent Collaborative Coding System[/bold cyan]\n"
        "[dim]Architect -> Coder -> Reviewer -> Tester[/dim]"
    )
    console.print(Panel(banner, border_style="cyan", padding=(1, 2)))


def display_results(state: AgentState, elapsed: float) -> None:
    """Display the final results in a formatted output.

    Args:
        state: The final workflow state.
        elapsed: Wall-clock time in seconds.
    """
    console.print("\n")
    console.print(Panel("[bold green]Pipeline Complete[/bold green]", border_style="green"))

    # Summary table
    table = Table(title="Run Summary", border_style="cyan")
    table.add_column("Metric", style="bold")
    table.add_column("Value")

    table.add_row("Status", state.final_status)
    table.add_row("Files Generated", str(len(state.files)))
    table.add_row("Test Files", str(len(state.test_files)))
    table.add_row("Review Cycles", str(state.review_count))
    table.add_row("Time Elapsed", f"{elapsed:.1f}s")
    table.add_row("Input Tokens", f"{state.total_input_tokens:,}")
    table.add_row("Output Tokens", f"{state.total_output_tokens:,}")

    input_cost = (state.total_input_tokens / 1_000_000) * INPUT_COST_PER_M
    output_cost = (state.total_output_tokens / 1_000_000) * OUTPUT_COST_PER_M
    total_cost = input_cost + output_cost
    table.add_row("Estimated Cost", f"${total_cost:.4f}")

    console.print(table)

    # Generated files
    if state.files:
        console.print("\n[bold cyan]Generated Files:[/bold cyan]")
        for filepath, content in state.files.items():
            lang = "python" if filepath.endswith(".py") else "text"
            console.print(f"\n[bold]{filepath}[/bold]")
            console.print(Syntax(content, lang, theme="monokai", line_numbers=True))

    # Test files
    if state.test_files:
        console.print("\n[bold magenta]Test Files:[/bold magenta]")
        for filepath, content in state.test_files.items():
            console.print(f"\n[bold]{filepath}[/bold]")
            console.print(Syntax(content, "python", theme="monokai", line_numbers=True))

    # Review feedback
    if state.review_feedback:
        console.print("\n[bold yellow]Last Review Feedback:[/bold yellow]")
        console.print(Panel(state.review_feedback, border_style="yellow"))

    # Errors
    if state.errors:
        console.print("\n[bold red]Errors Encountered:[/bold red]")
        for err in state.errors:
            console.print(f"  [red]- {err}[/red]")


def main() -> None:
    """Run the multi-agent coding pipeline."""
    display_banner()

    # Get task from CLI args or interactive prompt
    if len(sys.argv) > 1:
        task = " ".join(sys.argv[1:])
    else:
        task = console.input("[bold cyan]Enter your coding task:[/bold cyan] ")

    if not task.strip():
        console.print("[red]No task provided. Exiting.[/red]")
        sys.exit(1)

    console.print(f"\n[bold]Task:[/bold] {task}\n")
    console.print("[dim]Starting pipeline...[/dim]\n")

    # Build and run the graph
    graph = build_graph()
    initial_state = {"task": task}

    start_time = time.time()

    try:
        result = graph.invoke(initial_state)
    except Exception as e:
        console.print(f"\n[bold red]Pipeline failed: {e}[/bold red]")
        sys.exit(1)

    elapsed = time.time() - start_time

    # Convert result to AgentState for display
    final_state = AgentState(**result)
    display_results(final_state, elapsed)


if __name__ == "__main__":
    main()
