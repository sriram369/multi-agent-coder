"""FastAPI server exposing the multi-agent coding system as a REST API."""

from __future__ import annotations

from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel, Field

from orchestrator.graph import build_graph
from orchestrator.state import AgentState

load_dotenv()

app = FastAPI(
    title="Multi-Agent Collaborative Coder",
    description="AI-powered collaborative coding system with Architect, Coder, Reviewer, and Tester agents.",
    version="1.0.0",
)


class TaskRequest(BaseModel):
    """Request body for the /generate endpoint."""
    task: str = Field(..., description="The coding task to generate code for.")


class GenerateResponse(BaseModel):
    """Response body for the /generate endpoint."""
    status: str
    files: dict[str, str]
    test_files: dict[str, str]
    test_results: str
    architecture_plan: str
    review_feedback: str
    review_cycles: int
    total_input_tokens: int
    total_output_tokens: int
    errors: list[str]


@app.get("/health")
def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/generate", response_model=GenerateResponse)
def generate(request: TaskRequest) -> GenerateResponse:
    """Run the full multi-agent pipeline for a coding task.

    Args:
        request: The task request containing the coding task description.

    Returns:
        The complete pipeline results including generated files and test results.
    """
    graph = build_graph()
    result = graph.invoke({"task": request.task})
    state = AgentState(**result)

    return GenerateResponse(
        status=state.final_status,
        files=state.files,
        test_files=state.test_files,
        test_results=state.test_results,
        architecture_plan=state.architecture_plan,
        review_feedback=state.review_feedback,
        review_cycles=state.review_count,
        total_input_tokens=state.total_input_tokens,
        total_output_tokens=state.total_output_tokens,
        errors=state.errors,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
