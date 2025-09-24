"""Basic tests to ensure package imports work."""

def test_package_imports():
    """Test that the main package can be imported."""
    try:
        import win_mcp_server
        assert True
    except ImportError:
        assert False, "Failed to import win_mcp_server package"

def test_basic_functionality():
    """Basic test that always passes."""
    assert 1 + 1 == 2
