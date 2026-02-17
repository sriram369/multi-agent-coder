"""Reviewer agent — reviews generated code for bugs, security, and quality."""

from __future__ import annotations

from orchestrator.state import AgentState
from prompts.system_prompts import REVIEWER_SYSTEM_PROMPT

from agents.base import BaseAgent


class ReviewerAgent(BaseAgent):
    """Reviews code for bugs, security vulnerabilities, and best practices.

    Outputs a severity rating and specific feedback. If issues are found,
    code is sent back to the Coder for fixes (up to MAX_REVIEW_CYCLES).
    """

    def __init__(self) -> None:
        super().__init__("reviewer")

    def run(self, state: AgentState) -> dict:
        """Review the generated code and provide feedback.

        Args:
            state: Current workflow state containing files to review.

        Returns:
            Partial state update with review feedback and incremented count.
        """
        self.log(f"Reviewing {len(state.files)} file(s) (review cycle {state.review_count + 1})...")

        files_listing = "\n\n".join(
            f"### {path}\n```python\n{content}\n```"
            for path, content in state.files.items()
        )

        prompt = (
            f"ORIGINAL TASK:\n{state.task}\n\n"
            f"CODE TO REVIEW:\n{files_listing}"
        )

        try:
            feedback = self.call_llm(
                system_prompt=REVIEWER_SYSTEM_PROMPT,
                user_message=prompt,
            )

            self.log("Review complete.")

            severity = "pass"
            feedback_upper = feedback.upper()
            if "SEVERITY: MAJOR_ISSUES" in feedback_upper:
                severity = "major_issues"
                self.log("[red]Major issues found — sending back to Coder.[/red]")
            elif "SEVERITY: MINOR_ISSUES" in feedback_upper:
                severity = "minor_issues"
                self.log("[yellow]Minor issues found — sending back to Coder.[/yellow]")
            else:
                self.log("[green]Code passed review![/green]")

            return {
                "review_feedback": feedback,
                "review_count": state.review_count + 1,
                "current_agent": "reviewer",
                "messages": [
                    {
                        "agent": "reviewer",
                        "type": "review",
                        "content": f"Severity: {severity}",
                    }
                ],
                "total_input_tokens": state.total_input_tokens + self.total_input_tokens,
                "total_output_tokens": state.total_output_tokens + self.total_output_tokens,
            }

        except Exception as e:
            self.log(f"[red]Review failed: {e}[/red]")
            return {
                "review_feedback": "Review failed — proceeding to testing.",
                "review_count": state.review_count + 1,
                "current_agent": "reviewer",
                "errors": [f"Reviewer error: {e}"],
                "messages": [
                    {"agent": "reviewer", "type": "error", "content": str(e)}
                ],
            }
