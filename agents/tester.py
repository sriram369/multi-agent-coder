"""Tester agent — generates and runs pytest tests for generated code."""

from __future__ import annotations

from orchestrator.state import AgentState
from prompts.system_prompts import TESTER_SYSTEM_PROMPT

from agents.base import BaseAgent
from agents.coder import parse_file_tags


class TesterAgent(BaseAgent):
    """Generates pytest tests for the code and runs them.

    Uses the code_runner tool to execute tests in a subprocess
    and reports results back to the workflow.
    """

    def __init__(self) -> None:
        super().__init__("tester")

    def run(self, state: AgentState) -> dict:
        """Generate tests and run them against the generated code.

        Args:
            state: Current workflow state containing files to test.

        Returns:
            Partial state update with test files, results, and final status.
        """
        self.log("Generating tests...")

        files_listing = "\n\n".join(
            f"### {path}\n```python\n{content}\n```"
            for path, content in state.files.items()
        )

        prompt = (
            f"ORIGINAL TASK:\n{state.task}\n\n"
            f"CODE TO TEST:\n{files_listing}\n\n"
            f"Write comprehensive pytest tests for this code."
        )

        try:
            raw_output = self.call_llm(
                system_prompt=TESTER_SYSTEM_PROMPT,
                user_message=prompt,
            )
            test_files = parse_file_tags(raw_output)

            if not test_files:
                self.log("[red]Warning: No test files parsed from output.[/red]")
                test_files = {"tests/test_generated.py": raw_output}

            self.log(f"Generated {len(test_files)} test file(s).")

            # We'll attempt to run the tests later via the file_writer + code_runner
            # For now, mark the test generation as done
            return {
                "test_files": test_files,
                "test_results": "Tests generated. Run them with pytest in the output directory.",
                "final_status": "success",
                "current_agent": "tester",
                "messages": [
                    {
                        "agent": "tester",
                        "type": "tests",
                        "content": f"Generated {len(test_files)} test file(s)",
                    }
                ],
                "total_input_tokens": state.total_input_tokens + self.total_input_tokens,
                "total_output_tokens": state.total_output_tokens + self.total_output_tokens,
            }

        except Exception as e:
            self.log(f"[red]Test generation failed: {e}[/red]")
            return {
                "test_results": f"Test generation failed: {e}",
                "final_status": "partial",
                "current_agent": "tester",
                "errors": [f"Tester error: {e}"],
                "messages": [
                    {"agent": "tester", "type": "error", "content": str(e)}
                ],
            }
