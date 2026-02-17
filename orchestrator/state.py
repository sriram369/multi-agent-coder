"""Shared state schema for the multi-agent workflow."""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, Field


def _merge_dicts(left: dict[str, str], right: dict[str, str]) -> dict[str, str]:
    """Merge two dicts, with right taking precedence."""
    merged = dict(left)
    merged.update(right)
    return merged


def _append_lists(left: list[str], right: list[str]) -> list[str]:
    """Append right list to left list."""
    return left + right


def _append_messages(
    left: list[dict[str, str]], right: list[dict[str, str]]
) -> list[dict[str, str]]:
    """Append message lists."""
    return left + right


class AgentState(BaseModel):
    """Shared state passed through the entire LangGraph workflow.

    This is the single source of truth for all agent interactions.
    LangGraph reducers (via Annotated) handle merging when nodes
    return partial state updates.
    """

    task: str = ""
    architecture_plan: str = ""
    files: Annotated[dict[str, str], _merge_dicts] = Field(default_factory=dict)
    review_feedback: str = ""
    review_count: int = 0
    test_results: str = ""
    test_files: Annotated[dict[str, str], _merge_dicts] = Field(default_factory=dict)
    final_status: str = ""
    messages: Annotated[list[dict[str, str]], _append_messages] = Field(
        default_factory=list
    )
    current_agent: str = ""
    errors: Annotated[list[str], _append_lists] = Field(default_factory=list)
    total_input_tokens: int = 0
    total_output_tokens: int = 0
