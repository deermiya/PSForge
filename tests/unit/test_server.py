"""Basic unit tests for PSForge server components."""

import pytest


class TestRegistry:
    """Test tool registration system."""

    def test_register_tool_function(self):
        """Test that register_tool correctly registers a tool."""
        from psforge.registry import register_tool

        class MockMCP:
            def __init__(self):
                self.tools = {}

            def tool(self, name, description):
                def decorator(func):
                    self.tools[name] = {"func": func, "description": description}
                    return func

                return decorator

        mcp = MockMCP()

        def sample_tool(param: str) -> dict:
            """Sample tool for testing."""
            return {"success": True, "param": param}

        tool_name = register_tool(mcp, sample_tool, "test_tool")

        assert tool_name == "test_tool"
        assert "test_tool" in mcp.tools
        assert mcp.tools["test_tool"]["func"] == sample_tool


class TestDecorators:
    """Test decorators for error handling and logging."""

    def test_debug_tool_success(self):
        """Test debug_tool decorator with successful execution."""
        from psforge.decorators import debug_tool

        @debug_tool
        def successful_function():
            return {"success": True, "message": "OK"}

        result = successful_function()

        assert result["success"] is True
        assert result["message"] == "OK"

    def test_debug_tool_exception(self):
        """Test debug_tool decorator with exception."""
        from psforge.decorators import debug_tool

        @debug_tool
        def failing_function():
            raise ValueError("Test error")

        result = failing_function()

        assert result["success"] is False
        assert "error" in result
        assert "Test error" in result["error"]
        assert "detailed_error" in result


class TestUtils:
    """Test utility functions."""

    def test_validate_numeric_range_valid(self):
        """Test numeric range validation with valid values."""
        from psforge.ps_adapter.utils import validate_numeric_range

        # Should not raise
        validate_numeric_range(50, 0, 100, "test_param")
        validate_numeric_range(0, 0, 100, "test_param")
        validate_numeric_range(100, 0, 100, "test_param")

    def test_validate_numeric_range_invalid(self):
        """Test numeric range validation with invalid values."""
        from psforge.ps_adapter.utils import validate_numeric_range

        with pytest.raises(ValueError):
            validate_numeric_range(-1, 0, 100, "test_param")

        with pytest.raises(ValueError):
            validate_numeric_range(101, 0, 100, "test_param")

    def test_validate_color_channel_valid(self):
        """Test color channel validation with valid values."""
        from psforge.ps_adapter.utils import validate_color_channel

        # Should not raise
        validate_color_channel(0, "red")
        validate_color_channel(128, "green")
        validate_color_channel(255, "blue")

    def test_validate_color_channel_invalid(self):
        """Test color channel validation with invalid values."""
        from psforge.ps_adapter.utils import validate_color_channel

        with pytest.raises(ValueError):
            validate_color_channel(-1, "red")

        with pytest.raises(ValueError):
            validate_color_channel(256, "blue")

    def test_js_escape_string(self):
        """Test JavaScript string escaping."""
        from psforge.ps_adapter.utils import js_escape_string

        # Basic escaping
        assert js_escape_string('hello') == 'hello'
        assert js_escape_string('hello "world"') == 'hello \\"world\\"'
        assert js_escape_string('line1\\nline2') == 'line1\\\\nline2'
        assert js_escape_string('line1\nline2') == 'line1\\nline2'


class TestAppMetadata:
    """Test application metadata."""

    def test_version_format(self):
        """Test version string format."""
        from psforge.app import __version__

        assert isinstance(__version__, str)
        assert len(__version__) > 0
        # Should be in format like "0.1.0"
        parts = __version__.split(".")
        assert len(parts) >= 2

    def test_app_name(self):
        """Test application name."""
        from psforge.app import __app_name__

        assert __app_name__ == "PSForge"

    def test_description(self):
        """Test application description."""
        from psforge.app import __description__

        assert isinstance(__description__, str)
        assert len(__description__) > 0
