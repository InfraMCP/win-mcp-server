"""Tests for WinRM MCP Server."""

import pytest

from winrm_mcp_server import __version__


def test_version():
    """Test that version is defined."""
    assert __version__ == "0.2.0"


def test_import():
    """Test that main function can be imported."""
    from winrm_mcp_server import main

    assert callable(main)
