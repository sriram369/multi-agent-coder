"""Architect agent — analyzes tasks and creates implementation plans."""

from __future__ import annotations

from orchestrator.state import AgentState
from prompts.system_prompts import ARCHITECT_SYSTEM_PROMPT

from agents.base import BaseAgent


class ArchitectAgent(BaseAgent):
    """Analyzes user tasks and produces detailed architecture plans.

    The architect creates a structured plan including technology choices,
    file structure, design decisions, and step-by-step implementation order.
    """

    def __init__(self) -> None:
        super().__init__("architect")

    def run(self, state: AgentState) -> dict:
        """Generate an architecture plan from the user's task.

        Args:
            state: Current workflow state containing the task.

        Returns:
            Partial state update with architecture_plan and metadata.
        """
        self.log(f"Analyzing task: {state.task[:80]}...")

        try:
            plan = self.call_llm(
                system_prompt=ARCHITECT_SYSTEM_PROMPT,
                user_message=f"Create a detailed implementation plan for this task:\n\n{state.task}",
            )
            self.log("Architecture plan created successfully.")

            return {
                "architecture_plan": plan,
                "current_agent": "architect",
                "messages": [
                    {
                        "agent": "architect",
                        "type": "plan",
                        "content": plan[:200] + "...",
                    }
                ],
                "total_input_tokens": state.total_input_tokens + self.total_input_tokens,
                "total_output_tokens": state.total_output_tokens + self.total_output_tokens,
            }

        except Exception as e:
            self.log(f"[red]Failed to create plan: {e}[/red]")
            return {
                "architecture_plan": "",
                "current_agent": "architect",
                "errors": [f"Architect error: {e}"],
                "messages": [
                    {"agent": "architect", "type": "error", "content": str(e)}
                ],
            }
