"""Streamlit web UI for the Multi-Agent Collaborative Coding System."""

from __future__ import annotations

import os
import time
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr

import streamlit as st

# Must be first Streamlit call
st.set_page_config(
    page_title="Multi-Agent Coder",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

from orchestrator.graph import build_graph
from orchestrator.state import AgentState

# Cost per million tokens for Claude Sonnet 4
INPUT_COST_PER_M = 3.00
OUTPUT_COST_PER_M = 15.00

EXAMPLE_TASKS = [
    "Build a simple Python REST API using FastAPI that manages a todo list. Include CRUD endpoints with Pydantic validation.",
    "Create a Python CLI calculator with add, subtract, multiply, divide operations and error handling.",
    "Build a URL shortener API with FastAPI. Generate short codes, redirect to original URLs, and track click counts.",
    "Create a Python weather data parser that reads JSON weather data and generates summary statistics.",
]


def run_pipeline(task: str, api_key: str) -> AgentState:
    """Run the full multi-agent pipeline.

    Args:
        task: The coding task description.
        api_key: Anthropic API key.

    Returns:
        The final AgentState after pipeline completion.
    """
    os.environ["ANTHROPIC_API_KEY"] = api_key
    graph = build_graph()
    result = graph.invoke({"task": task})
    return AgentState(**result)


def main() -> None:
    """Main Streamlit application."""

    # --- Sidebar ---
    with st.sidebar:
        st.markdown("## ⚙️ Configuration")

        # Use secret key silently if available — never expose it in the UI
        has_secret_key = hasattr(st, "secrets") and "ANTHROPIC_API_KEY" in st.secrets

        if has_secret_key:
            api_key = st.secrets["ANTHROPIC_API_KEY"]
            st.success("API key configured", icon="🔑")
        else:
            api_key = st.text_input(
                "Anthropic API Key",
                type="password",
                placeholder="sk-ant-...",
                help="Your Anthropic API key. Never stored — only used for this session.",
            )

        st.markdown("---")
        st.markdown("## 📋 Example Tasks")
        for i, example in enumerate(EXAMPLE_TASKS):
            if st.button(f"Example {i + 1}", key=f"example_{i}", use_container_width=True):
                st.session_state["task_input"] = example

        st.markdown("---")
        st.markdown(
            "## 🏗️ Architecture\n"
            "```\n"
            "User Task\n"
            "  → Architect (plans)\n"
            "  → Coder (writes code)\n"
            "  → Reviewer (reviews)\n"
            "  → Coder (fixes, up to 2x)\n"
            "  → Tester (writes tests)\n"
            "  → Output\n"
            "```"
        )

        st.markdown("---")
        st.markdown(
            "Built with [LangGraph](https://langchain-ai.github.io/langgraph/) "
            "& [Claude Sonnet 4](https://anthropic.com)"
        )

    # --- Header ---
    st.markdown(
        "<h1 style='text-align: center;'>🤖 Multi-Agent Collaborative Coder</h1>"
        "<p style='text-align: center; color: gray;'>"
        "4 AI agents collaborate to plan, code, review, and test your project"
        "</p>",
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.markdown("##### 🔵 Architect\nPlans & designs")
    col2.markdown("##### 🟢 Coder\nWrites code")
    col3.markdown("##### 🟡 Reviewer\nFinds bugs")
    col4.markdown("##### 🟣 Tester\nWrites tests")

    st.markdown("---")

    # --- Task Input ---
    task = st.text_area(
        "Describe your coding task:",
        value=st.session_state.get("task_input", ""),
        height=100,
        placeholder="e.g., Build a REST API for a todo app with FastAPI...",
    )

    run_button = st.button("🚀 Generate Code", type="primary", use_container_width=True)

    if run_button:
        if not api_key:
            st.error("Please enter your Anthropic API key in the sidebar.")
            return
        if not task.strip():
            st.error("Please enter a coding task.")
            return

        # --- Run Pipeline ---
        progress_bar = st.progress(0, text="Starting pipeline...")
        agent_status = st.empty()
        log_container = st.container()

        steps = [
            ("🔵 Architect is planning...", 0.15),
            ("🟢 Coder is writing code...", 0.35),
            ("🟡 Reviewer is checking code...", 0.55),
            ("🟢 Coder is fixing issues...", 0.70),
            ("🟡 Reviewer re-checking...", 0.80),
            ("🟣 Tester is writing tests...", 0.90),
            ("📁 Writing files...", 0.95),
        ]

        # Show animated progress while pipeline runs
        with log_container:
            step_placeholder = st.empty()

        start_time = time.time()

        try:
            # Start progress animation in a separate display
            for step_text, step_pct in steps[:1]:
                progress_bar.progress(step_pct, text=step_text)

            result = run_pipeline(task, api_key)
            elapsed = time.time() - start_time

            progress_bar.progress(1.0, text="✅ Pipeline complete!")

        except Exception as e:
            progress_bar.progress(1.0, text="❌ Pipeline failed")
            st.error(f"Pipeline error: {e}")
            return

        # --- Display Results ---
        st.markdown("---")
        st.markdown("## 📊 Results")

        # Metrics row
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Status", result.final_status.upper())
        m2.metric("Code Files", len(result.files))
        m3.metric("Test Files", len(result.test_files))
        m4.metric("Review Cycles", result.review_count)
        m5.metric("Time", f"{elapsed:.0f}s")

        # Cost
        input_cost = (result.total_input_tokens / 1_000_000) * INPUT_COST_PER_M
        output_cost = (result.total_output_tokens / 1_000_000) * OUTPUT_COST_PER_M
        total_cost = input_cost + output_cost

        c1, c2, c3 = st.columns(3)
        c1.metric("Input Tokens", f"{result.total_input_tokens:,}")
        c2.metric("Output Tokens", f"{result.total_output_tokens:,}")
        c3.metric("Estimated Cost", f"${total_cost:.4f}")

        # Architecture Plan
        with st.expander("🔵 Architecture Plan", expanded=False):
            st.markdown(result.architecture_plan)

        # Generated Code
        st.markdown("### 🟢 Generated Code")
        if result.files:
            tabs = st.tabs(list(result.files.keys()))
            for tab, (filename, content) in zip(tabs, result.files.items()):
                with tab:
                    lang = "python" if filename.endswith(".py") else "text"
                    if filename.endswith(".txt"):
                        lang = "text"
                    elif filename.endswith(".md"):
                        lang = "markdown"
                    st.code(content, language=lang, line_numbers=True)
        else:
            st.warning("No code files generated.")

        # Test Files
        if result.test_files:
            st.markdown("### 🟣 Test Files")
            tabs = st.tabs(list(result.test_files.keys()))
            for tab, (filename, content) in zip(tabs, result.test_files.items()):
                with tab:
                    st.code(content, language="python", line_numbers=True)

        # Review Feedback
        with st.expander("🟡 Review Feedback", expanded=False):
            st.markdown(result.review_feedback)

        # Errors
        if result.errors:
            with st.expander("❌ Errors", expanded=True):
                for err in result.errors:
                    st.error(err)

        # Download button
        st.markdown("---")
        st.markdown("### 📥 Download")

        # Build a combined output string
        all_code = ""
        for filename, content in {**result.files, **result.test_files}.items():
            all_code += f"# {'=' * 60}\n# FILE: {filename}\n# {'=' * 60}\n\n{content}\n\n"

        st.download_button(
            label="Download All Generated Code",
            data=all_code,
            file_name="generated_code.py",
            mime="text/plain",
            use_container_width=True,
        )


if __name__ == "__main__":
    main()
