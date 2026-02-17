"""Coder agent — writes production code from architecture plans."""

from __future__ import annotations

import re

from orchestrator.state import AgentState
from prompts.system_prompts import CODER_FIX_PROMPT, CODER_SYSTEM_PROMPT

from agents.base import BaseAgent


def parse_file_tags(text: str) -> dict[str, str]:
    """Parse XML-style file tags from the coder's output.

    Handles edge cases like code containing XML-like strings,
    multiple files, and nested directory paths.

    Args:
        text: Raw LLM output containing <file path="...">...</file> tags.

    Returns:
        Dict mapping file paths to their contents.
    """
    files: dict[str, str] = {}
    # Match <file path="...">content</file> — using DOTALL for multiline content
    pattern = r'<file\s+path=["\']([^"\']+)["\']\s*>(.*?)</file>'
    matches = re.findall(pattern, text, re.DOTALL)

    for filepath, content in matches:
        # Strip leading/trailing whitespace but preserve internal formatting
        cleaned = content.strip("\n")
        files[filepath.strip()] = cleaned

    return files


class CoderAgent(BaseAgent):
    """Takes the architect's plan and writes actual code file by file.

    If review feedback exists in state, fixes the issues mentioned
    and regenerates the relevant files.
    """

    def __init__(self) -> None:
        super().__init__("coder")

    def run(self, state: AgentState) -> dict:
        """Generate or fix code based on the architecture plan.

        Args:
            state: Current workflow state.

        Returns:
            Partial state update with generated files.
        """
        is_fix = bool(state.review_feedback and state.review_count > 0)

        if is_fix:
            self.log(f"Fixing code based on review feedback (cycle {state.review_count})...")
            prompt = self._build_fix_prompt(state)
            system = CODER_FIX_PROMPT
        else:
            self.log("Generating code from architecture plan...")
            prompt = self._build_initial_prompt(state)
            system = CODER_SYSTEM_PROMPT

        try:
            raw_output = self.call_llm(system_prompt=system, user_message=prompt)
            files = parse_file_tags(raw_output)

            if not files:
                self.log("[red]Warning: No files parsed from output. Storing raw output.[/red]")
                files = {"raw_output.txt": raw_output}

            self.log(f"Generated {len(files)} file(s): {', '.join(files.keys())}")

            return {
                "files": files,
                "current_agent": "coder",
                "messages": [
                    {
                        "agent": "coder",
                        "type": "fix" if is_fix else "code",
                        "content": f"Generated {len(files)} files",
                    }
                ],
                "total_input_tokens": state.total_input_tokens + self.total_input_tokens,
                "total_output_tokens": state.total_output_tokens + self.total_output_tokens,
            }

        except Exception as e:
            self.log(f"[red]Failed to generate code: {e}[/red]")
            return {
                "current_agent": "coder",
                "errors": [f"Coder error: {e}"],
                "messages": [
                    {"agent": "coder", "type": "error", "content": str(e)}
                ],
            }

    def _build_initial_prompt(self, state: AgentState) -> str:
        """Build the prompt for initial code generation."""
        return (
            f"Here is the architecture plan. Write ALL the code files.\n\n"
            f"ORIGINAL TASK:\n{state.task}\n\n"
            f"ARCHITECTURE PLAN:\n{state.architecture_plan}"
        )

    def _build_fix_prompt(self, state: AgentState) -> str:
        """Build the prompt for code fixes based on review feedback."""
        files_listing = "\n\n".join(
            f"### {path}\n```python\n{content}\n```"
            for path, content in state.files.items()
        )
        return (
            f"ORIGINAL TASK:\n{state.task}\n\n"
            f"ARCHITECTURE PLAN:\n{state.architecture_plan}\n\n"
            f"CURRENT CODE:\n{files_listing}\n\n"
            f"REVIEWER FEEDBACK:\n{state.review_feedback}\n\n"
            f"Fix ALL issues mentioned above. Output only the changed files."
        )
