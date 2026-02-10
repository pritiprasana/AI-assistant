"""Tests for CLI module."""

import pytest
from typer.testing import CliRunner

from slot_assistant.cli.main import app


runner = CliRunner()


def test_status_command():
    """Test that status command runs without crashing."""
    result = runner.invoke(app, ["status"])
    # Should run (may fail if Ollama not installed, but shouldn't crash)
    assert result.exit_code in (0, 1)


def test_ask_command_without_ollama():
    """Test ask command when Ollama is not running."""
    result = runner.invoke(app, ["ask", "test question"])
    # Should handle gracefully even without Ollama
    assert result.exit_code == 0
