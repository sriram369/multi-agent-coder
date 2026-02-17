"""Agent implementations for the multi-agent coding system."""

__all__ = ["ArchitectAgent", "CoderAgent", "ReviewerAgent", "TesterAgent"]


def __getattr__(name: str):
    """Lazy imports to avoid circular dependency."""
    if name == "ArchitectAgent":
        from agents.architect import ArchitectAgent
        return ArchitectAgent
    if name == "CoderAgent":
        from agents.coder import CoderAgent
        return CoderAgent
    if name == "ReviewerAgent":
        from agents.reviewer import ReviewerAgent
        return ReviewerAgent
    if name == "TesterAgent":
        from agents.tester import TesterAgent
        return TesterAgent
    raise AttributeError(f"module 'agents' has no attribute {name!r}")
