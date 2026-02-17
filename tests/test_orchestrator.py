"""Tests for the multi-agent orchestrator system."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from agents.coder import parse_file_tags
from orchestrator.state import AgentState
from tools.file_manager import clean_output_dir, read_file, write_files


class TestParseFileTags:
    """Tests for the XML file tag parser."""

    def test_single_file(self) -> None:
        text = '<file path="main.py">print("hello")</file>'
        result = parse_file_tags(text)
        assert result == {"main.py": 'print("hello")'}

    def test_multiple_files(self) -> None:
        text = (
            '<file path="a.py">code_a</file>\n'
            '<file path="b.py">code_b</file>'
        )
        result = parse_file_tags(text)
        assert len(result) == 2
        assert result["a.py"] == "code_a"
        assert result["b.py"] == "code_b"

    def test_nested_directories(self) -> None:
        text = '<file path="app/models/user.py">class User: pass</file>'
        result = parse_file_tags(text)
        assert "app/models/user.py" in result

    def test_multiline_content(self) -> None:
        text = '<file path="main.py">\nimport os\n\ndef main():\n    pass\n</file>'
        result = parse_file_tags(text)
        assert "import os" in result["main.py"]
        assert "def main():" in result["main.py"]

    def test_no_files(self) -> None:
        result = parse_file_tags("no file tags here")
        assert result == {}

    def test_single_quotes(self) -> None:
        text = "<file path='main.py'>code</file>"
        result = parse_file_tags(text)
        assert result == {"main.py": "code"}


class TestAgentState:
    """Tests for the Pydantic state model."""

    def test_default_state(self) -> None:
        state = AgentState()
        assert state.task == ""
        assert state.files == {}
        assert state.review_count == 0
        assert state.errors == []

    def test_state_with_values(self) -> None:
        state = AgentState(task="build an API", review_count=1)
        assert state.task == "build an API"
        assert state.review_count == 1


class TestFileManager:
    """Tests for the file management tools."""

    def test_write_and_read(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            files = {"hello.py": "print('hello')", "sub/module.py": "x = 1"}
            written = write_files(files, tmpdir)

            assert len(written) == 2
            assert read_file(str(Path(tmpdir) / "hello.py")) == "print('hello')"
            assert read_file(str(Path(tmpdir) / "sub" / "module.py")) == "x = 1"

    def test_clean_output_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = str(Path(tmpdir) / "output")
            Path(test_dir).mkdir()
            (Path(test_dir) / "old.txt").write_text("old")

            clean_output_dir(test_dir)
            assert Path(test_dir).exists()
            assert list(Path(test_dir).iterdir()) == []
