"""Base agent class with shared logic for all agents."""

from __future__ import annotations

import os
import time
from abc import ABC, abstractmethod

import anthropic
from dotenv import load_dotenv
from rich.console import Console

from orchestrator.state import AgentState

load_dotenv()

# Agent color mapping
AGENT_COLORS: dict[str, str] = {
    "architect": "blue",
    "coder": "green",
    "reviewer": "yellow",
    "tester": "magenta",
}

console = Console()


class BaseAgent(ABC):
    """Base class for all agents in the multi-agent system.

    Provides shared functionality including LLM calls with retry logic,
    Rich console logging, and token tracking.
    """

    def __init__(self, name: str) -> None:
        self.name = name
        self.color = AGENT_COLORS.get(name, "white")
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = os.getenv("MODEL_NAME", "claude-sonnet-4-20250514")
        self.max_tokens = int(os.getenv("MAX_TOKENS", "8096"))
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    def log(self, message: str) -> None:
        """Log a message with the agent's assigned color."""
        console.print(f"[bold {self.color}][{self.name.upper()}][/bold {self.color}] {message}")

    def call_llm(self, system_prompt: str, user_message: str) -> str:
        """Call the Anthropic API with retry logic.

        Args:
            system_prompt: The system prompt for the LLM.
            user_message: The user message to send.

        Returns:
            The text content of the LLM response.

        Raises:
            anthropic.APIError: If all retries are exhausted.
        """
        max_retries = 2
        last_error: Exception | None = None

        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    wait = 2 ** attempt
                    self.log(f"Retry {attempt}/{max_retries} after {wait}s...")
                    time.sleep(wait)

                self.log("Calling LLM...")
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_message}],
                )

                input_tokens = response.usage.input_tokens
                output_tokens = response.usage.output_tokens
                self.total_input_tokens += input_tokens
                self.total_output_tokens += output_tokens

                self.log(
                    f"Tokens used — input: {input_tokens:,}, output: {output_tokens:,}"
                )

                text = response.content[0].text
                return text

            except anthropic.APIError as e:
                last_error = e
                self.log(f"[red]API error: {e}[/red]")
                if attempt == max_retries:
                    raise
            except Exception as e:
                last_error = e
                self.log(f"[red]Unexpected error: {e}[/red]")
                if attempt == max_retries:
                    raise

        # Should never reach here, but just in case
        raise last_error  # type: ignore[misc]

    @abstractmethod
    def run(self, state: AgentState) -> dict:
        """Run the agent and return partial state updates.

        Args:
            state: The current shared agent state.

        Returns:
            A dict of state fields to update.
        """
        ...
